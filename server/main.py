"""
ArbTrader - FastAPI Application Entry Point
"""
from src.infrastructure.redis.client import redis_client
import structlog
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config import settings
from src.core.logging import configure_logging
from src.infrastructure.database.session import engine
from src.api.v1.router import api_router

configure_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    logger.info("ArbTrader starting up", env=settings.APP_ENV)
    yield
    logger.info("ArbTrader shutting down")
    await redis_client.aclose()
    await engine.dispose()

app = FastAPI(
    title="ArbTrader API",
    description="Arbitrage intelligence platform for trading cards",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# class CatchAllMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         try:
#             return await call_next(request)
#         except Exception as exc:
#             logger.error(
#                 "Unhandled exception caught by middleware",
#                 path=request.url.path,
#                 error=str(exc),
#             )
#             return JSONResponse(
#                 status_code=500,
#                 content={"detail": "Internal server error", "error": type(exc).__name__},
#             )

# app.add_middleware(CatchAllMiddleware)

# ── CORS (registered second = outermost in the stack) ─────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "env": settings.APP_ENV}
