"""
FX currency converter - converts prices to GBP using live rates.
Falls back to hardcoded rates in mock mode.
"""
from typing import Dict
import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import settings

logger = structlog.get_logger(__name__)

# Fallback rates (to GBP)
FALLBACK_RATES: Dict[str, float] = {
    "GBP": 1.0,
    "USD": 0.79,
    "EUR": 0.86,
    "JPY": 0.0053,
    "CAD": 0.58,
    "AUD": 0.51,
}


class FXConverter:
    """
    Converts foreign currency amounts to GBP.
    Uses exchangerate.host API in production, hardcoded fallback in mock mode.
    """

    def __init__(self):
        self._rates: Dict[str, float] = FALLBACK_RATES.copy()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def refresh_rates(self) -> None:
        """Fetch latest FX rates from the API."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://api.exchangerate.host/latest",
                    params={"base": "GBP", "access_key": settings.FX_API_KEY},
                )
                resp.raise_for_status()
                data = resp.json()
                if data.get("success"):
                    # Rates are quoted as X per 1 GBP - invert for to-GBP conversion
                    raw = data.get("rates", {})
                    self._rates = {k: 1.0 / v for k, v in raw.items() if v > 0}
                    self._rates["GBP"] = 1.0
                    logger.info("FX rates refreshed", count=len(self._rates))
        except Exception as e:
            logger.warning("FX rate refresh failed, using fallback rates", error=str(e))
            self._rates = FALLBACK_RATES.copy()

    def to_gbp(self, amount: float, currency: str) -> float:
        """Convert an amount from a given currency to GBP."""
        rate = self._rates.get(currency.upper(), FALLBACK_RATES.get(currency.upper(), 1.0))
        return round(amount * rate, 2)

    def get_rate(self, currency: str) -> float:
        """Return the GBP conversion rate for a given currency."""
        return self._rates.get(currency.upper(), 1.0)


# Singleton instance
fx_converter = FXConverter()
