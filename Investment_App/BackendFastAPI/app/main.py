"""
app/main.py
───────────
FastAPI application factory.

Broker adapters self-register when their modules are imported here.
To add a new broker, import its module below — that is the only change needed.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import router as v1_router
from app.core.config import get_settings
from app.core.exceptions import BrokerAuthError, BrokerError, BrokerNotFoundError
from app.core.logger import get_logger
from app.db.init_db import init_db

# ── Import broker adapters so they self-register ───────────────────────────────
import app.brokers.upstox  # noqa: F401
import app.brokers.etoro   # noqa: F401
# To add a new broker, add one line: `import app.brokers.<name>`

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(
        "Starting Investment Portfolio API — env=%s log_level=%s",
        settings.app_env,
        settings.log_level,
    )
    init_db()
    yield
    logger.info("Shutting down Investment Portfolio API")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Investment Portfolio API",
        description=(
            "Multi-broker portfolio backend. "
            "Normalises holdings, positions, and trades from any registered broker."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────
    allow_origins = ["*"] if settings.app_env == "development" else []
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception handlers ────────────────────────────────────────────────
    @app.exception_handler(BrokerNotFoundError)
    async def broker_not_found_handler(request: Request, exc: BrokerNotFoundError):
        return JSONResponse(
            status_code=404,
            content={"status": "error", "error": {"code": "BROKER_NOT_FOUND", "message": str(exc)}},
        )

    @app.exception_handler(BrokerAuthError)
    async def broker_auth_handler(request: Request, exc: BrokerAuthError):
        return JSONResponse(
            status_code=401,
            content={
                "status": "error",
                "error": {"code": "BROKER_AUTH_ERROR", "broker": exc.broker, "message": str(exc)},
            },
        )

    @app.exception_handler(BrokerError)
    async def broker_error_handler(request: Request, exc: BrokerError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "error": {"code": "BROKER_ERROR", "broker": exc.broker, "message": str(exc)},
            },
        )

    # ── Routes ────────────────────────────────────────────────────────────
    app.include_router(v1_router)

    @app.get("/health", tags=["system"])
    async def health():
        return {"status": "ok", "version": "1.0.0"}

    return app


app = create_app()
