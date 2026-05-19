"""API v1 - aggregated router mounting all domain routers."""
from fastapi import APIRouter

from src.domains.users.router import router as users_router
from src.domains.cards.router import router as cards_router
from src.domains.markets.router import router as markets_router
from src.domains.pricing.router import router as pricing_router
from src.domains.arbitrage.router import router as arbitrage_router
from src.domains.alerts.router import router as alerts_router
from src.domains.portfolio.router import router as portfolio_router
from src.domains.automation.router import router as automation_router

api_router = APIRouter()

api_router.include_router(users_router)
api_router.include_router(cards_router)
api_router.include_router(markets_router)
api_router.include_router(pricing_router)
api_router.include_router(arbitrage_router)
api_router.include_router(alerts_router)
api_router.include_router(portfolio_router)
api_router.include_router(automation_router)
