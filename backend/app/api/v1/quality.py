"""
Data quality API endpoints for AirIndex India.

Endpoints:
  GET /api/v1/data-quality — Coverage and quality summaries
"""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Query

from app.schemas.responses import ApiEnvelope, QualitySummaryResponse
from app.services.quality_service import QualityService

router = APIRouter(prefix="/data-quality", tags=["Data Quality"])

_quality_service = QualityService()


@router.get(
    "",
    response_model=ApiEnvelope[QualitySummaryResponse],
    summary="Data quality summary",
    description="Returns coverage metrics, quality score distributions, "
                "and outlier/duplicate statistics for a period.",
)
def get_data_quality(
    start_date: date = Query(
        default=None,
        description="Start date (inclusive). Defaults to today.",
    ),
    end_date: date = Query(
        default=None,
        description="End date (inclusive). Defaults to today.",
    ),
):
    """Get data quality summary for a period."""
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date

    data = _quality_service.get_quality_summary(start_date, end_date)
    return ApiEnvelope(data=data)
