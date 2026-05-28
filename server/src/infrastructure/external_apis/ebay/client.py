"""
eBay Browse API client - fetches active listings for UK and US markets.
"""
import base64
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

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

_cached_token: Optional[str] = None
_token_expires_at: Optional[datetime] = None


class EbayClient:
    """
    eBay Browse API client for fetching active card listings.
    Requires OAuth Client Credentials token (EBAY_CLIENT_ID / EBAY_CLIENT_SECRET in .env).
    Raises on failure so tenacity can retry.
    """

    def __init__(self, region: str = "UK"):
        self.region = region
        self.base_url = EBAY_BROWSE_ENDPOINTS[region]
        self.marketplace_id = EBAY_MARKETPLACE_IDS[region]

    async def _get_app_token(self) -> str:
        """Fetch or return a cached eBay OAuth application access token.

        Raises RuntimeError if credentials are missing or the token request fails.
        """
        global _cached_token, _token_expires_at

        if _cached_token and _token_expires_at and datetime.now(timezone.utc) < _token_expires_at:
            return _cached_token

        client_id = settings.EBAY_CLIENT_ID
        client_secret = settings.EBAY_CLIENT_SECRET

        if not client_id or not client_secret:
            raise RuntimeError("EBAY_CLIENT_ID or EBAY_CLIENT_SECRET is not configured in .env")

        is_sandbox = "SBX" in client_id
        token_url = (
            "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
            if is_sandbox
            else "https://api.ebay.com/identity/v1/oauth2/token"
        )

        encoded_creds = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

        async with httpx.AsyncClient(timeout=15.0) as client:
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
            _cached_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 7200)
            _token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in - 300)
            logger.info("eBay OAuth token refreshed", expires_in=expires_in)
            return _cached_token

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=20))
    async def get_completed_listings(
        self, card_name: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Fetch active listings for a card from eBay Browse API.

        Retries up to 3 times on any failure. Returns an empty list only when
        eBay genuinely returns zero results (not on error).
        """
        token = await self._get_app_token()

        async with httpx.AsyncClient(timeout=30.0) as client:
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
                    "X-EBAY-C-ENDUSERCTX": f"contextualLocation=country={'GB' if self.region == 'UK' else 'US'}",
                    "Content-Type": "application/json",
                },
            )
            logger.info(
                "eBay Browse API response",
                status=resp.status_code,
                region=self.region,
                card=card_name,
            )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("itemSummaries", [])
            logger.info(
                "eBay listings fetched",
                card=card_name,
                region=self.region,
                count=len(items),
            )
            return [self._parse_item(item) for item in items]

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
            "listing_type": item.get("buyingOptions", [None])[0],
            "region": self.region,
        }
