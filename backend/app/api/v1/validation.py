"""
Validation / backtest API endpoints for AirIndex India.

Endpoints:
  GET /api/v1/validation — Backtest/reference validation summaries
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Query

from app.schemas.responses import ApiEnvelope, ValidationSummaryResponse
from app.services.index_service import IndexService

router = APIRouter(prefix="/validation", tags=["Validation"])

_index_service = IndexService()


@router.get(
    "",
    response_model=ApiEnvelope[ValidationSummaryResponse],
    summary="Backtest validation summary",
    description="Returns summary statistics from backtest index "
                "calculations. Actual DGCA reference comparison will "
                "be available when reference data is supplied.",
)
def get_validation_summary(
    start_date: date = Query(
        default=None,
        description="Start date (inclusive). Defaults to 7 days ago.",
    ),
    end_date: date = Query(
        default=None,
        description="End date (inclusive). Defaults to today.",
    ),
):
    """Get backtest/validation summary for a date range."""
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date - timedelta(days=6)

    daily_results = _index_service.compute_date_range(start_date, end_date)

    # Compute summary statistics
    index_values = [
        r.index_value for r in daily_results
        if r.index_value is not None
    ]

    avg_value = None
    min_value = None
    max_value = None
    avg_coverage = None

    if index_values:
        avg_value = Decimal(str(round(
            sum(float(v) for v in index_values) / len(index_values), 4
        )))
        min_value = min(index_values)
        max_value = max(index_values)

    coverages = [float(r.coverage_pct) for r in daily_results]
    if coverages:
        avg_coverage = Decimal(str(round(sum(coverages) / len(coverages), 2)))

    total_obs = sum(r.observation_count for r in daily_results)
    route_count = daily_results[0].route_count if daily_results else 0

    data = ValidationSummaryResponse(
        period_start=start_date,
        period_end=end_date,
        backtest_days=len(daily_results),
        average_index_value=avg_value,
        min_index_value=min_value,
        max_index_value=max_value,
        average_coverage_pct=avg_coverage,
        route_count=route_count,
        total_observations=total_obs,
        status="prototype",
    )
    return ApiEnvelope(data=data)
