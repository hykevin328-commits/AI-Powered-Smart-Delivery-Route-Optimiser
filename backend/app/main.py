"""
FastAPI application entry point.

Wires together:
  - All API routers
  - Authentication router
  - WebSocket router
  - CORS, GZip, TrustedHost middleware
  - Centralised exception handlers
  - Startup / shutdown lifecycle hooks
  - Health & readiness probes
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.api import (
    analytics,
    assignments,
    customers,
    maps,
    orders,
    predictions,
    routes,
    traffic,
    vehicles,
)
from app.auth.router import router as auth_router
from app.config.database import engine
from app.config.logging import get_logger, setup_logging
from app.config.redis_client import close_redis, get_redis
from app.config.settings import settings
from app.utils.exception_handlers import register_exception_handlers
from app.websocket.router import router as ws_router

logger = get_logger(__name__)


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # ── Startup ───────────────────────────────────────────────────────────────
    setup_logging()
    logger.info(
        "startup",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        env=settings.APP_ENV,
    )

    # Warm up Redis connection
    try:
        redis = await get_redis()
        await redis.ping()
        logger.info("redis_connected", url=settings.REDIS_URL)
    except Exception as exc:
        logger.warning("redis_unavailable", error=str(exc))

    # Verify DB reachability (connection pool pre-ping is automatic,
    # but we do a lightweight select 1 to surface config errors early)
    try:
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import AsyncSession
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("database_connected")
    except Exception as exc:
        logger.error("database_connection_failed", error=str(exc))

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("shutdown", app=settings.APP_NAME)
    await close_redis()
    await engine.dispose()


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Production-ready REST + WebSocket API for an AI-Powered Smart "
            "Delivery Route Optimizer. Includes JWT auth, Google OR-Tools "
            "TSP/VRP optimization, real-time WebSocket updates, AI predictions, "
            "traffic integration, and analytics dashboards."
        ),
        docs_url="/docs" if settings.APP_ENV != "production" else None,
        redoc_url="/redoc" if settings.APP_ENV != "production" else None,
        openapi_url="/openapi.json" if settings.APP_ENV != "production" else None,
        lifespan=lifespan,
        contact={
            "name": "Smart Route Optimizer Team",
            "email": "support@routeoptimizer.io",
        },
        license_info={"name": "MIT"},
        servers=[
            {"url": "http://localhost:8000", "description": "Local development"},
            {"url": "https://api.routeoptimizer.io", "description": "Production"},
        ],
    )

    # ── Middleware ─────────────────────────────────────────────────────────────

    # CORS – allow configured origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # GZip responses > 1 KB
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    # Trusted hosts (prevents Host-header injection in production)
    if settings.APP_ENV == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["api.routeoptimizer.io", "*.routeoptimizer.io"],
        )

    # Request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Process-Time-Ms"] = str(elapsed)
        return response

    # ── Exception handlers ─────────────────────────────────────────────────────
    register_exception_handlers(app)

    # ── Routers ────────────────────────────────────────────────────────────────
    API_V1 = "/api/v1"

    # Auth
    app.include_router(auth_router, prefix=API_V1)

    # Core delivery domain
    app.include_router(orders.router, prefix=API_V1)
    app.include_router(assignments.router, prefix=API_V1)
    app.include_router(customers.router, prefix=API_V1)
    app.include_router(vehicles.router, prefix=API_V1)

    # Route optimisation
    app.include_router(routes.router, prefix=API_V1)

    # Maps & geocoding
    app.include_router(maps.router, prefix=API_V1)

    # AI predictions
    app.include_router(predictions.router, prefix=API_V1)

    # Traffic
    app.include_router(traffic.router, prefix=API_V1)

    # Analytics
    app.include_router(analytics.router, prefix=API_V1)

    # WebSocket (no version prefix – standard practice for WS)
    app.include_router(ws_router)

    # ── Utility endpoints ──────────────────────────────────────────────────────

    @app.get("/health", tags=["Health"], summary="Liveness probe")
    async def health():
        return JSONResponse(
            content={
                "status": "healthy",
                "app": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "env": settings.APP_ENV,
            }
        )

    @app.get("/ready", tags=["Health"], summary="Readiness probe")
    async def ready():
        checks: dict = {}

        # DB
        try:
            from sqlalchemy import text
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            checks["database"] = "ok"
        except Exception as exc:
            checks["database"] = f"error: {exc}"

        # Redis
        try:
            redis = await get_redis()
            await redis.ping()
            checks["redis"] = "ok"
        except Exception as exc:
            checks["redis"] = f"error: {exc}"

        all_ok = all(v == "ok" for v in checks.values())
        return JSONResponse(
            content={"status": "ready" if all_ok else "degraded", "checks": checks},
            status_code=200 if all_ok else 503,
        )

    @app.get("/", tags=["Health"], include_in_schema=False)
    async def root():
        return {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "health": "/health",
        }

    return app


# ── Module-level app instance (used by uvicorn / gunicorn) ────────────────────
app: FastAPI = create_app()
