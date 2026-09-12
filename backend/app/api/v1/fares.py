"""
Fares API endpoints for AirIndex India.

Endpoints:
  GET /api/v1/fares — Paginated, policy-safe fare observation view
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Query

from app.schemas.responses import (
    ApiEnvelope,
    ApiMeta,
    FareObservationResponse,
)
from app.services.fare_service import FareService

router = APIRouter(prefix="/fares", tags=["Fares"])

_fare_service = FareService()


@router.get(
    "",
    response_model=ApiEnvelope[list[FareObservationResponse]],
    summary="Paginated fare observations",
    description="Returns fare observations with optional filters for "
                "date, route, and airline. Sensitive raw payloads and "
                "internal fields are excluded.",
)
def get_fares(
    observation_date: Optional[date] = Query(
        default=None,
        description="Observation date. Defaults to today.",
    ),
    route: Optional[str] = Query(
        default=None,
        description="Route code filter (e.g., DEL-BOM).",
    ),
    airline: Optional[str] = Query(
        default=None,
        description="Airline code filter (e.g., 6E).",
    ),
    page: int = Query(
        default=1, ge=1,
        description="Page number.",
    ),
    per_page: int = Query(
        default=50, ge=1, le=500,
        description="Items per page.",
    ),
):
    """Get paginated fare observations."""
    data, pagination = _fare_service.get_observations(
        observation_date=observation_date,
        route_code=route,
        airline_code=airline,
        page=page,
        per_page=per_page,
    )
    return ApiEnvelope(
        data=data,
        meta=ApiMeta(pagination=pagination),
    )
