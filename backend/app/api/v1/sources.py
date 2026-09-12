"""
Sources API endpoints for AirIndex India.

Endpoints:
  GET /api/v1/sources/status — Connector health and authorization
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter

from app.core.config_loader import load_all_configs
from app.schemas.responses import ApiEnvelope, SourceStatusResponse

router = APIRouter(prefix="/sources", tags=["Sources"])


@router.get(
    "/status",
    response_model=ApiEnvelope[list[SourceStatusResponse]],
    summary="Source connector status",
    description="Returns the health and authorization status of all "
                "configured data sources. Sensitive internal details "
                "are excluded.",
)
def get_sources_status():
    """Get connector health and compliance status for all sources."""
    config_dir = Path(__file__).resolve().parent.parent.parent.parent.parent / "configs"
    config = load_all_configs(config_dir)

    data = [
        SourceStatusResponse(
            code=s.code,
            source_type=s.type.value,
            enabled=s.enabled,
            compliance_status=s.compliance_status.value,
            rate_limit_per_minute=s.rate_limit_per_minute,
            health="healthy" if s.enabled else "disabled",
        )
        for s in config.sources.sources
    ]
    return ApiEnvelope(data=data)
