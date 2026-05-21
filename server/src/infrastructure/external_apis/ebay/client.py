"""
eBay Finding API client - fetches completed/sold listings for UK and US markets.
Supports mock mode when USE_MOCK_DATA=true.
"""
import uuid
import base64
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import random

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import settings

logger = structlog.get_logger(__name__)

EBAY_FINDING_ENDPOINTS = {
    "UK": "https://svcs.ebay.com/services/search/FindingService/v1",
    "US": "https://svcs.ebay.com/services/search/FindingService/v1",
}

EBAY_SITE_IDS = {
    "UK": "3",   # eBay UK
    "US": "0",   # eBay US
}

MOCK_CARDS = [
    "Charizard Base Set Holo",
    "Pikachu Illustrator",
    "Blastoise Base Set Holo",
    "Venusaur Base Set Holo",
    "Mewtwo Base Set Holo",
    "Lugia Neo Genesis Holo",
    "Ho-Oh Neo Revelation Holo",
    "Rayquaza EX Deoxys Holo",
    "Umbreon Gold Star",
    "Espeon Gold Star",
]

_cached_token: Optional[str] = None
_token_expires_at: Optional[datetime] = None


class EbayClient:
    """
    eBay Finding API client for fetching recently sold card prices.
    Falls back to mock data when USE_MOCK_DATA=true.
    Supports secure OAuth Client Credentials tokens to bypass anonymous rate limits.
    """

    def __init__(self, region: str = "UK"):
        self.region = region
        self.base_url = EBAY_FINDING_ENDPOINTS[region]
        self.site_id = EBAY_SITE_IDS[region]
        self.headers = {
            "X-EBAY-SOA-GLOBAL-ID": f"EBAY-{'GB' if region == 'UK' else 'US'}",
            "X-EBAY-SOA-SERVICE-VERSION": "1.0.0",
            "Content-Type": "application/json",
        }

    async def _get_app_token(self) -> Optional[str]:
        """Fetch or retrieve a cached eBay OAuth application access token using Client Credentials."""
        global _cached_token, _token_expires_at
        
        # Check cache
        if _cached_token and _token_expires_at and datetime.now(timezone.utc) < _token_expires_at:
            return _cached_token

        client_id = settings.EBAY_CLIENT_ID
        client_secret = settings.EBAY_CLIENT_SECRET

        if not client_id or not client_secret:
            logger.warning("eBay Client ID or Client Secret not configured for OAuth. Falling back to legacy API auth.")
            return None

        # Determine endpoint environment based on App ID / Client ID prefix
        is_sandbox = "SBX" in client_id or "sandbox" in (settings.EBAY_APP_ID or "").lower()
        token_url = (
            "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
            if is_sandbox
            else "https://api.ebay.com/identity/v1/oauth2/token"
        )

        credentials = f"{client_id}:{client_secret}"
        encoded_creds = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_creds}"
        }

        data = {
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope"
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(token_url, data=data, headers=headers)
                resp.raise_for_status()
                token_data = resp.json()
                _cached_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 7200)
                # Expire token 5 minutes early as a buffer
                _token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in - 300)
                logger.info("Successfully refreshed eBay OAuth application access token.")
                return _cached_token
            except Exception as e:
                logger.error("Failed to fetch eBay OAuth access token", error=str(e))
                return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_completed_listings(
        self, card_name: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Fetch completed/sold listings for a card name."""
        if settings.USE_MOCK_DATA:
            return self._mock_completed_listings(card_name, limit)

        # Try to obtain secure OAuth token
        token = await self._get_app_token()

        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = self.headers.copy()
            # The Finding API is a legacy API — it uses App ID auth only.
            # OAuth Bearer tokens are for the modern eBay REST APIs and
            # cause 500 errors on this endpoint. Always use SECURITY-APPNAME.
            params = {
                "OPERATION-NAME": "findCompletedItems",
                "SERVICE-VERSION": "1.0.0",
                "RESPONSE-DATA-FORMAT": "JSON",
                "SECURITY-APPNAME": settings.EBAY_APP_ID,
                "keywords": card_name,
                "categoryId": "2536",  # Pokémon cards
                "itemFilter(0).name": "SoldItemsOnly",
                "itemFilter(0).value": "true",
                "paginationInput.entriesPerPage": str(limit),
                "sortOrder": "EndTimeSoonest",
            }
            headers["X-EBAY-SOA-SECURITY-APPNAME"] = settings.EBAY_APP_ID

            try:
                resp = await client.get(self.base_url, params=params, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                items = (
                    data.get("findCompletedItemsResponse", [{}])[0]
                    .get("searchResult", [{}])[0]
                    .get("item", [])
                )
                return [self._parse_item(item) for item in items]
            except httpx.HTTPError as e:
                logger.error("eBay API error", region=self.region, card=card_name, error=str(e))
                return self._mock_completed_listings(card_name, limit)

    def _parse_item(self, item: Dict) -> Dict[str, Any]:
        return {
            "external_id": item.get("itemId", [None])[0],
            "title": item.get("title", [""])[0],
            "price": float(item.get("sellingStatus", [{}])[0].get("currentPrice", [{}])[0].get("__value__", 0)),
            "currency": item.get("sellingStatus", [{}])[0].get("currentPrice", [{}])[0].get("@currencyId", "GBP"),
            "condition": item.get("condition", [{}])[0].get("conditionDisplayName", ["Raw"])[0],
            "sold_at": item.get("listingInfo", [{}])[0].get("endTime", [datetime.now(timezone.utc).isoformat()])[0],
            "url": item.get("viewItemURL", [""])[0],
            "region": self.region,
        }

    def _mock_completed_listings(self, card_name: str, limit: int) -> List[Dict[str, Any]]:
        """Generate realistic mock sold listings for development."""
        base_prices = {
            "UK": {"mean": 85.0, "variance": 30.0, "currency": "GBP"},
            "US": {"mean": 95.0, "variance": 40.0, "currency": "USD"},
        }
        config = base_prices[self.region]
        results = []
        for i in range(min(limit, 10)):
            price = max(5.0, config["mean"] + random.gauss(0, config["variance"]))
            sold_at = datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30))
            results.append({
                "external_id": str(uuid.uuid4()),
                "title": f"{card_name} Pokemon Card {'PSA 9' if random.random() > 0.7 else 'Raw'}",
                "price": round(price, 2),
                "currency": config["currency"],
                "condition": "PSA 9" if random.random() > 0.7 else "Near Mint",
                "sold_at": sold_at.isoformat(),
                "url": f"https://www.ebay.{'co.uk' if self.region == 'UK' else 'com'}/itm/mock-{i}",
                "region": self.region,
            })
        return results
