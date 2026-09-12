"""
Quality service for AirIndex India.

Provides data quality metrics and summaries for API endpoints.

Status: DEMO / PROTOTYPE / ASSUMPTION
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Optional

from app.core.config_loader import load_all_configs
from app.core.enums import QualityStatus
from app.schemas.responses import QualitySummaryResponse
from app.services.mock_fare_generator import MockFareGenerator
from app.services.pipeline import FarePipeline


class QualityService:
    """Service for data quality monitoring and reporting."""

    def __init__(self, seed: int = 42):
        self.generator = MockFareGenerator(seed=seed)
        self.pipeline = FarePipeline()

    def _get_config(self):
        config_dir = Path(__file__).resolve().parent.parent.parent.parent / "configs"
        return load_all_configs(config_dir)

    def get_quality_summary(
        self,
        start_date: date,
        end_date: date,
    ) -> QualitySummaryResponse:
        """Get quality summary for a date range.

        In this prototype, generates mock data and processes it to compute
        quality metrics. In production, this would query pre-computed
        quality tables.
        """
        config = self._get_config()

        routes = [
            {"code": r.code, "origin": r.origin, "destination": r.destination}
            for r in config.routes.routes
        ]
        airlines = [
            {"code": a.code, "name": a.name, "active": a.active}
            for a in config.airlines.airlines
        ]
        advance_days = config.advance_windows.advance_purchase_days

        # Use just the start_date for efficiency in prototype
        raw_obs = self.generator.generate_day(
            observation_date=start_date,
            routes=routes,
            airlines=airlines,
            advance_days=advance_days,
        )
        pipeline_result = self.pipeline.process(raw_obs)

        # Compute quality metrics
        valid_count = 0
        flagged_count = 0
        outlier_count = 0
        quality_scores: list[float] = []
        coverage_route: dict[str, int] = defaultdict(int)
        coverage_source: dict[str, int] = defaultdict(int)

        for scored in pipeline_result.valid:
            obs = scored.observation
            quality_scores.append(float(scored.quality_score))

            if obs.quality_status == QualityStatus.VALID:
                valid_count += 1
            else:
                flagged_count += 1

            if scored.is_outlier:
                outlier_count += 1

            route_key = f"{obs.origin_airport}-{obs.destination_airport}"
            coverage_route[route_key] += 1
            coverage_source[obs.source_code] += 1

        avg_score = None
        if quality_scores:
            avg_score = Decimal(str(round(sum(quality_scores) / len(quality_scores), 2)))

        return QualitySummaryResponse(
            period_start=start_date,
            period_end=end_date,
            total_observations=pipeline_result.total_input,
            valid_count=valid_count,
            flagged_count=flagged_count,
            invalid_count=len(pipeline_result.invalid),
            outlier_count=outlier_count,
            duplicate_count=pipeline_result.duplicates_removed,
            average_quality_score=avg_score,
            coverage_by_route=dict(coverage_route),
            coverage_by_source=dict(coverage_source),
        )
