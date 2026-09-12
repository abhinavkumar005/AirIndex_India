"""
Index API endpoints for AirIndex India.

Endpoints:
  GET /api/v1/index/current   — Latest composite APIx
  GET /api/v1/index/daily     — Daily index series
  GET /api/v1/index/weekly    — Weekly index series
  GET /api/v1/index/monthly   — Monthly index series
  GET /api/v1/index/history   — Filtered multi-frequency history
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Query

from app.schemas.responses import (
    ApiEnvelope,
    CurrentIndexResponse,
    IndexValueResponse,
)
from app.services.index_service import IndexService

router = APIRouter(prefix="/index", tags=["Index"])

# Shared service instance (prototype — in production, use dependency injection)
_service = IndexService()


@router.get(
    "/current",
    response_model=ApiEnvelope[CurrentIndexResponse],
    summary="Latest composite APIx value",
    description="Returns the most recent publishable composite airfare price "
                "index with coverage metadata and trend indicators.",
)
def get_current_index():
    """Get the latest daily APIx value with 7-day and 30-day trends."""
    data = _service.get_current_index()
    return ApiEnvelope(data=data)


@router.get(
    "/daily",
    response_model=ApiEnvelope[list[IndexValueResponse]],
    summary="Daily index series",
    description="Returns daily index values for a given date range.",
)
def get_daily_index(
    start_date: date = Query(
        default=None,
        description="Start date (inclusive). Defaults to 7 days ago.",
    ),
    end_date: date = Query(
        default=None,
        description="End date (inclusive). Defaults to today.",
    ),
):
    """Get daily index values for a date range."""
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=6)

    data = _service.get_daily_series(start_date, end_date)
    return ApiEnvelope(data=data)


@router.get(
    "/weekly",
    response_model=ApiEnvelope[list[IndexValueResponse]],
    summary="Weekly index series",
    description="Returns weekly aggregated index values for a date range.",
)
def get_weekly_index(
    start_date: date = Query(
        default=None,
        description="Start date (inclusive). Defaults to 28 days ago.",
    ),
    end_date: date = Query(
        default=None,
        description="End date (inclusive). Defaults to today.",
    ),
):
    """Get weekly index values for a date range."""
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=27)

    data = _service.get_weekly_series(start_date, end_date)
    return ApiEnvelope(data=data)


@router.get(
    "/monthly",
    response_model=ApiEnvelope[list[IndexValueResponse]],
    summary="Monthly index series",
    description="Returns monthly aggregated index values for a date range.",
)
def get_monthly_index(
    start_date: date = Query(
        default=None,
        description="Start date (inclusive). Defaults to 90 days ago.",
    ),
    end_date: date = Query(
        default=None,
        description="End date (inclusive). Defaults to today.",
    ),
):
    """Get monthly index values for a date range."""
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=89)

    data = _service.get_monthly_series(start_date, end_date)
    return ApiEnvelope(data=data)


@router.get(
    "/history",
    response_model=ApiEnvelope[list[IndexValueResponse]],
    summary="Filtered multi-frequency index history",
    description="Returns index values filtered by frequency and date range.",
)
def get_index_history(
    frequency: str = Query(
        default="daily",
        description="Index frequency: daily, weekly, or monthly.",
    ),
    start_date: date = Query(
        default=None,
        description="Start date (inclusive).",
    ),
    end_date: date = Query(
        default=None,
        description="End date (inclusive).",
    ),
):
    """Get filtered index history by frequency and date range."""
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        if frequency == "monthly":
            start_date = end_date - timedelta(days=89)
        elif frequency == "weekly":
            start_date = end_date - timedelta(days=27)
        else:
            start_date = end_date - timedelta(days=6)

    if frequency == "weekly":
        data = _service.get_weekly_series(start_date, end_date)
    elif frequency == "monthly":
        data = _service.get_monthly_series(start_date, end_date)
    else:
        data = _service.get_daily_series(start_date, end_date)

    return ApiEnvelope(data=data)
