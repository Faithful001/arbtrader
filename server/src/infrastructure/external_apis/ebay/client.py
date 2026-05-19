"""
eBay Finding API client - fetches completed/sold listings for UK and US markets.
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


class EbayClient:
    """
    eBay Finding API client for fetching recently sold card prices.
    Falls back to mock data when USE_MOCK_DATA=true.
    """

    def __init__(self, region: str = "UK"):
        self.region = region
        self.base_url = EBAY_FINDING_ENDPOINTS[region]
        self.site_id = EBAY_SITE_IDS[region]
        self.headers = {
            "X-EBAY-SOA-SECURITY-APPNAME": settings.EBAY_APP_ID,
            "X-EBAY-SOA-GLOBAL-ID": f"EBAY-{'GB' if region == 'UK' else 'US'}",
            "X-EBAY-SOA-SERVICE-VERSION": "1.0.0",
            "Content-Type": "application/json",
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_completed_listings(
        self, card_name: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Fetch completed/sold listings for a card name."""
        if settings.USE_MOCK_DATA:
            return self._mock_completed_listings(card_name, limit)

        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {
                "OPERATION-NAME": "findCompletedItems",
                "SERVICE-VERSION": "1.0.0",
                "SECURITY-APPNAME": settings.EBAY_APP_ID,
                "RESPONSE-DATA-FORMAT": "JSON",
                "keywords": card_name,
                "categoryId": "2536",  # Pokémon cards
                "itemFilter(0).name": "SoldItemsOnly",
                "itemFilter(0).value": "true",
                "paginationInput.entriesPerPage": str(limit),
                "sortOrder": "EndTimeSoonest",
            }
            try:
                resp = await client.get(self.base_url, params=params, headers=self.headers)
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
