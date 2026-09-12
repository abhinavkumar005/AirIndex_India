"""
Routes API endpoints for AirIndex India.

Endpoints:
  GET /api/v1/routes              — Configured route basket
  GET /api/v1/routes/{route}/trend — Route-level fare/index trend
"""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Path, Query

from app.schemas.responses import (
    ApiEnvelope,
    RouteResponse,
    RouteTrendResponse,
)
from app.services.index_service import IndexService
from app.services.route_service import RouteService

router = APIRouter(prefix="/routes", tags=["Routes"])

_route_service = RouteService()
_index_service = IndexService()


@router.get(
    "",
    response_model=ApiEnvelope[list[RouteResponse]],
    summary="Configured route basket",
    description="Returns all routes in the current index basket with their "
                "weights and effective dates.",
)
def get_routes():
    """Get the configured route basket."""
    data = _route_service.get_routes()
    return ApiEnvelope(data=data)


@router.get(
    "/{route}/trend",
    response_model=ApiEnvelope[RouteTrendResponse],
    summary="Route-level fare/index trend",
    description="Returns daily representative fare and price relative "
                "values for a specific route over a date range.",
)
def get_route_trend(
    route: str = Path(
        ..., description="Route code (e.g., DEL-BOM)"
    ),
    start_date: date = Query(
        default=None,
        description="Start date (inclusive). Defaults to 7 days ago.",
    ),
    end_date: date = Query(
        default=None,
        description="End date (inclusive). Defaults to today.",
    ),
):
    """Get fare/index trend for a specific route."""
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=6)

    data = _index_service.get_route_trend(route, start_date, end_date)
    return ApiEnvelope(data=data)
