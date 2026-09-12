"""
FastAPI application for AirIndex India.

Government-facing API for the Airfare Price Index (APIx) platform.
Provides versioned endpoints for index values, fare observations,
route basket, source status, data quality, and validation data.

Status: DEMO / PROTOTYPE / ASSUMPTION — not official production deployment.

Usage:
    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.index import router as index_router
from app.api.v1.routes import router as routes_router
from app.api.v1.fares import router as fares_router
from app.api.v1.sources import router as sources_router
from app.api.v1.quality import router as quality_router
from app.api.v1.validation import router as validation_router
from app.core.config import get_settings

logger = logging.getLogger("airindex.api")


def create_app() -> FastAPI:
    """Application factory for the AirIndex India API."""
    settings = get_settings()

    # Configure root logging unless the host process already has handlers.
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    app = FastAPI(
        title="AirIndex India API",
        description=(
            "Auditable Airfare Price Index (APIx) for Indian domestic routes. "
            "DEMO / PROTOTYPE / ASSUMPTION — not official MoSPI/PSD methodology. "
            "All data is synthetic unless explicitly stated otherwise."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS — explicit origins from settings (CORS_ORIGINS env / .env).
    # Empty list means no cross-origin access (fail closed). Credentials
    # are never combined with a wildcard origin.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=settings.allow_credentials,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    # Register v1 routers under /api/v1
    api_prefix = "/api/v1"
    app.include_router(index_router, prefix=api_prefix)
    app.include_router(routes_router, prefix=api_prefix)
    app.include_router(fares_router, prefix=api_prefix)
    app.include_router(sources_router, prefix=api_prefix)
    app.include_router(quality_router, prefix=api_prefix)
    app.include_router(validation_router, prefix=api_prefix)

    # Global exception handler — logs the traceback, returns a client-safe body
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        request_id = str(uuid.uuid4())[:8]
        logger.exception(
            "Unhandled exception on %s %s [request_id=%s]",
            request.method, request.url.path, request_id,
        )
        return JSONResponse(
            status_code=500,
            content={
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
                "request_id": request_id,
                "details": [],
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        request_id = str(uuid.uuid4())[:8]
        logger.warning(
            "Invalid request on %s %s [request_id=%s]: %s",
            request.method, request.url.path, request_id, exc,
        )
        return JSONResponse(
            status_code=400,
            content={
                "code": "VALIDATION_ERROR",
                "message": str(exc),
                "request_id": request_id,
                "details": [],
            },
        )

    # Health check
    @app.get("/health", tags=["Health"])
    def health_check():
        """Simple health check endpoint."""
        return {
            "status": "healthy",
            "version": "0.1.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prototype": True,
        }

    # Root
    @app.get("/", tags=["Root"])
    def root():
        """API root — redirects to documentation."""
        return {
            "name": "AirIndex India API",
            "version": "0.1.0",
            "status": "DEMO / PROTOTYPE",
            "docs": "/docs",
            "api_base": "/api/v1",
        }

    return app


# Module-level app instance for uvicorn
app = create_app()
