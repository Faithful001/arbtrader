"""
eBay Browse API client - fetches active listings for UK and US markets.
Supports mock mode when USE_MOCK_DATA=true.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import random

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import settings

logger = structlog.get_logger(__name__)

EBAY_BROWSE_ENDPOINTS = {
    "UK": "https://api.ebay.com/buy/browse/v1/item_summary/search",
    "US": "https://api.ebay.com/buy/browse/v1/item_summary/search",
}

EBAY_MARKETPLACE_IDS = {
    "UK": "EBAY_GB",
    "US": "EBAY_US",
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
    eBay Browse API client for fetching active card listings.
    Falls back to mock data when USE_MOCK_DATA=true.
    Requires OAuth Client Credentials token.
    """

    def __init__(self, region: str = "UK"):
        self.region = region
        self.base_url = EBAY_BROWSE_ENDPOINTS[region]
        self.marketplace_id = EBAY_MARKETPLACE_IDS[region]

    async def _get_app_token(self) -> Optional[str]:
        """Fetch or retrieve a cached eBay OAuth application access token."""
        global _cached_token, _token_expires_at

        if _cached_token and _token_expires_at and datetime.now(timezone.utc) < _token_expires_at:
            return _cached_token

        client_id = settings.EBAY_CLIENT_ID
        client_secret = settings.EBAY_CLIENT_SECRET

        if not client_id or not client_secret:
            logger.warning("eBay Client ID or Secret not configured.")
            return None

        import base64
        is_sandbox = "SBX" in client_id
        token_url = (
            "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
            if is_sandbox
            else "https://api.ebay.com/identity/v1/oauth2/token"
        )

        encoded_creds = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(
                    token_url,
                    data={
                        "grant_type": "client_credentials",
                        "scope": "https://api.ebay.com/oauth/api_scope",
                    },
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Authorization": f"Basic {encoded_creds}",
                    },
                )
                resp.raise_for_status()
                token_data = resp.json()
                _cached_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 7200)
                _token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in - 300)
                logger.info("eBay OAuth token refreshed")
                return _cached_token
            except Exception as e:
                logger.error("Failed to fetch eBay OAuth token", error=str(e))
                return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_completed_listings(
        self, card_name: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Fetch active listings for a card name."""
        if settings.USE_MOCK_DATA:
            return self._mock_completed_listings(card_name, limit)

        token = await self._get_app_token()
        if not token:
            logger.warning("No eBay token available, falling back to mock data")
            return self._mock_completed_listings(card_name, limit)

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.get(
                    self.base_url,
                    params={
                        "q": card_name,
                        "category_ids": "183454",  # Pokémon TCG category
                        "limit": str(limit),
                        "sort": "price",
                    },
                    headers={
                        "Authorization": f"Bearer {token}",
                        "X-EBAY-C-MARKETPLACE-ID": self.marketplace_id,
                        "X-EBAY-C-ENDUSERCTX": f"contextualLocation=country={('GB' if self.region == 'UK' else 'US')}",
                        "Content-Type": "application/json",
                    },
                )
                logger.info("eBay Browse API response", status=resp.status_code, region=self.region, card=card_name)
                resp.raise_for_status()
                data = resp.json()
                items = data.get("itemSummaries", [])
                return [self._parse_item(item) for item in items]

            except httpx.HTTPError as e:
                logger.error("eBay Browse API error", region=self.region, card=card_name, error=str(e))
                return self._mock_completed_listings(card_name, limit)

    def _parse_item(self, item: Dict) -> Dict[str, Any]:
        price_info = item.get("price", {})
        return {
            "external_id": item.get("itemId"),
            "title": item.get("title", ""),
            "price": float(price_info.get("value", 0)),
            "currency": price_info.get("currency", "GBP" if self.region == "UK" else "USD"),
            "condition": item.get("condition", "Unknown"),
            "sold_at": item.get("itemEndDate") or datetime.now(timezone.utc).isoformat(),
            "url": item.get("itemWebUrl", ""),
            "region": self.region,
        }

    def _mock_completed_listings(self, card_name: str, limit: int) -> List[Dict[str, Any]]:
        """Generate realistic mock listings for development."""
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