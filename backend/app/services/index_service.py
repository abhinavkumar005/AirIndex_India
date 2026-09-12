"""
Index service for AirIndex India.

Provides business logic for index calculation, retrieval, and formatting.
Bridges the IndexEngine with API endpoints.

Status: DEMO / PROTOTYPE / ASSUMPTION
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional

from app.core.config_loader import load_all_configs
from app.core.enums import IndexFrequency
from app.index_engine.engine import EngineConfig, IndexEngine, IndexResult
from app.schemas.responses import (
    CurrentIndexResponse,
    IndexValueResponse,
    RouteComponentResponse,
    RouteTrendPoint,
    RouteTrendResponse,
)
from app.services.mock_fare_generator import MockFareGenerator
from app.services.pipeline import FarePipeline


class IndexService:
    """Service for computing and retrieving index values.

    In this prototype, indices are computed on-the-fly from mock data.
    In production, results would be pre-computed and stored in the database.
    """

    def __init__(
        self,
        engine_config: EngineConfig | None = None,
        seed: int = 42,
    ):
        self.engine = IndexEngine(engine_config)
        self.pipeline = FarePipeline()
        self.generator = MockFareGenerator(seed=seed)

    def _get_routes_and_config(self) -> tuple[list[dict], list[dict], list[int], dict[str, float]]:
        """Load route/airline/window configuration from YAML files."""
        from pathlib import Path

        config_dir = Path(__file__).resolve().parent.parent.parent.parent / "configs"
        config = load_all_configs(config_dir)

        routes = [
            {"code": r.code, "origin": r.origin, "destination": r.destination}
            for r in config.routes.routes
        ]
        airlines = [
            {"code": a.code, "name": a.name, "active": a.active}
            for a in config.airlines.airlines
        ]
        advance_days = config.advance_windows.advance_purchase_days
        route_weights = {r.code: r.weight for r in config.routes.routes}

        return routes, airlines, advance_days, route_weights

    def compute_daily_index(
        self,
        observation_date: date,
        base_fares: dict[str, Decimal] | None = None,
    ) -> IndexResult:
        """Generate mock data, run pipeline, compute daily index."""
        routes, airlines, advance_days, route_weights = self._get_routes_and_config()

        observations = self.generator.generate_day(
            observation_date=observation_date,
            routes=routes,
            airlines=airlines,
            advance_days=advance_days,
        )

        pipeline_result = self.pipeline.process(observations)

        return self.engine.compute_daily(
            observation_date=observation_date,
            observations=pipeline_result.valid,
            route_weights=route_weights,
            base_fares=base_fares,
        )

    def compute_date_range(
        self,
        start_date: date,
        end_date: date,
        base_fares: dict[str, Decimal] | None = None,
    ) -> list[IndexResult]:
        """Compute daily indices for a date range.

        Base-period handling (prototype fallback, per the implementation
        plan): when no explicit base fares are supplied, the first day of
        the range is the anchor (index = 100) and every subsequent day is
        computed against that day's representative fares. This keeps
        within-series movements meaningful while `base_period` remains
        unresolved in index.yml.
        """
        results: list[IndexResult] = []
        active_base = base_fares
        current = start_date
        while current <= end_date:
            result = self.compute_daily_index(current, base_fares=active_base)
            if active_base is not None:
                result.base_period = f"first_observation:{start_date.isoformat()}"
            else:
                # First day anchors the series.
                result.base_period = f"first_observation:{current.isoformat()}"
                active_base = {
                    rr.route_code: rr.representative_fare
                    for rr in result.route_results
                    if rr.representative_fare is not None
                }
            results.append(result)
            current += timedelta(days=1)
        return results

    def get_current_index(self) -> CurrentIndexResponse:
        """Get the latest daily index value with trend indicators.

        All three values (current, 7-day-ago, 30-day-ago) are computed
        against a single base: the representative fares 30 days ago. The
        30-day-ago index is therefore 100 by construction, and the trends
        measure movement relative to that shared anchor.
        """
        today = date.today()
        month_ago = today - timedelta(days=30)
        week_ago = today - timedelta(days=7)

        # Anchor: 30 days ago, self-based (index = 100).
        month_result = self.compute_daily_index(month_ago)
        base_fares = {
            rr.route_code: rr.representative_fare
            for rr in month_result.route_results
            if rr.representative_fare is not None
        }
        base_label = f"first_observation:{month_ago.isoformat()}"
        month_result.base_period = base_label

        current = self.compute_daily_index(today, base_fares=base_fares)
        current.base_period = base_label

        # Compute 7-day and 30-day trends
        trend_7d = None
        trend_30d = None

        if current.index_value is not None:
            week_result = self.compute_daily_index(week_ago, base_fares=base_fares)
            week_result.base_period = base_label
            if week_result.index_value is not None:
                trend_7d = current.index_value - week_result.index_value
            if month_result.index_value is not None:
                trend_30d = current.index_value - month_result.index_value

        return CurrentIndexResponse(
            index_value=current.index_value,
            frequency=current.frequency,
            as_of=today,
            coverage_pct=current.coverage_pct,
            route_count=current.route_count,
            eligible_route_count=current.eligible_route_count,
            observation_count=current.observation_count,
            config_version=current.config_version,
            calculation_version=current.calculation_version,
            trend_7d=trend_7d,
            trend_30d=trend_30d,
        )

    def get_daily_series(
        self,
        start_date: date,
        end_date: date,
    ) -> list[IndexValueResponse]:
        """Get daily index values for a date range."""
        daily_results = self.compute_date_range(start_date, end_date)
        return [self._result_to_response(r) for r in daily_results]

    def get_weekly_series(
        self,
        start_date: date,
        end_date: date,
    ) -> list[IndexValueResponse]:
        """Get weekly index values for a date range."""
        daily_results = self.compute_date_range(start_date, end_date)

        weekly_results: list[IndexValueResponse] = []
        # Group by ISO week
        weeks: dict[tuple[int, int], list[IndexResult]] = defaultdict(list)
        for r in daily_results:
            iso = r.period_start.isocalendar()
            weeks[(iso[0], iso[1])].append(r)

        for (year, week), daily_in_week in sorted(weeks.items()):
            week_start = date.fromisocalendar(year, week, 1)
            weekly = self.engine.compute_weekly(week_start, daily_in_week)
            weekly_results.append(self._result_to_response(weekly))

        return weekly_results

    def get_monthly_series(
        self,
        start_date: date,
        end_date: date,
    ) -> list[IndexValueResponse]:
        """Get monthly index values for a date range."""
        daily_results = self.compute_date_range(start_date, end_date)

        monthly_results: list[IndexValueResponse] = []
        months: dict[tuple[int, int], list[IndexResult]] = defaultdict(list)
        for r in daily_results:
            months[(r.period_start.year, r.period_start.month)].append(r)

        for (year, month), daily_in_month in sorted(months.items()):
            monthly = self.engine.compute_monthly(year, month, daily_in_month)
            monthly_results.append(self._result_to_response(monthly))

        return monthly_results

    def get_route_trend(
        self,
        route_code: str,
        start_date: date,
        end_date: date,
    ) -> RouteTrendResponse:
        """Get fare/index trend for a specific route."""
        daily_results = self.compute_date_range(start_date, end_date)
        origin, destination = route_code.split("-") if "-" in route_code else ("", "")

        trend_points: list[RouteTrendPoint] = []
        for result in daily_results:
            route_result = next(
                (rr for rr in result.route_results if rr.route_code == route_code),
                None,
            )
            if route_result:
                trend_points.append(RouteTrendPoint(
                    date=result.period_start,
                    representative_fare=route_result.representative_fare,
                    price_relative=route_result.price_relative,
                    observation_count=route_result.observation_count,
                ))
            else:
                trend_points.append(RouteTrendPoint(
                    date=result.period_start,
                    observation_count=0,
                ))

        return RouteTrendResponse(
            route_code=route_code,
            origin=origin,
            destination=destination,
            trend=trend_points,
        )

    @staticmethod
    def _result_to_response(result: IndexResult) -> IndexValueResponse:
        """Convert engine IndexResult to API response model."""
        components = [
            RouteComponentResponse(
                route_code=rr.route_code,
                representative_fare=rr.representative_fare,
                base_fare=rr.base_fare,
                price_relative=rr.price_relative,
                weight=rr.weight,
                weighted_contribution=rr.weighted_contribution,
                observation_count=rr.observation_count,
                excluded_count=rr.excluded_count,
                is_eligible=rr.is_eligible,
                ineligibility_reason=rr.ineligibility_reason,
            )
            for rr in result.route_results
        ]

        return IndexValueResponse(
            frequency=result.frequency,
            period_start=result.period_start,
            period_end=result.period_end,
            index_value=result.index_value,
            base_period=result.base_period,
            config_version=result.config_version,
            calculation_version=result.calculation_version,
            coverage_pct=result.coverage_pct,
            route_count=result.route_count,
            eligible_route_count=result.eligible_route_count,
            observation_count=result.observation_count,
            route_components=components,
        )
