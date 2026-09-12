"""
Index calculation engine for AirIndex India (APIx).

Implements the methodology from STATISTICAL_METHODOLOGY.md:
  1. Group eligible observations into cells (route × period × lead-time)
  2. Compute representative fare per cell (median by default)
  3. Calculate price relatives against base-period representative fares
  4. Aggregate weighted price relatives into composite index values

Supports daily, weekly, and monthly index frequencies.

Status: DEMO / PROTOTYPE / ASSUMPTION — not official MoSPI/PSD methodology.

Usage:
    from app.index_engine.engine import IndexEngine
    engine = IndexEngine(config)
    results = engine.compute_daily(date(2026, 9, 14), observations, weights)
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from app.core.enums import AvailabilityStatus, IndexFrequency, QualityStatus
from app.services.pipeline import QualityScoredObservation


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class CellResult:
    """Result for a single route-cell in an index period."""
    route_code: str
    origin: str
    destination: str
    period_start: date
    period_end: date
    advance_days: int | None  # None for aggregated across all advance days
    observation_count: int
    excluded_count: int  # Outliers excluded from representative fare
    representative_fare: Decimal | None
    statistic_used: str  # e.g. "median"


@dataclass
class RouteIndexResult:
    """Index result for a single route."""
    route_code: str
    representative_fare: Decimal | None
    base_fare: Decimal | None
    price_relative: Decimal | None
    weight: float
    weighted_contribution: Decimal | None
    observation_count: int
    excluded_count: int
    cells: list[CellResult] = field(default_factory=list)
    is_eligible: bool = True
    ineligibility_reason: str | None = None


@dataclass
class IndexResult:
    """Complete index calculation result."""
    frequency: str
    period_start: date
    period_end: date
    index_value: Decimal | None
    base_period: str | None
    config_version: str
    calculation_version: str
    coverage_pct: Decimal
    route_count: int
    eligible_route_count: int
    observation_count: int
    route_results: list[RouteIndexResult] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Engine configuration
# ---------------------------------------------------------------------------

@dataclass
class EngineConfig:
    """Configuration for the index engine.

    Loaded from index.yml and routes.yml configuration.
    """
    representative_fare_statistic: str = "median"
    minimum_cell_observations: int = 1
    currency: str = "INR"
    base_period: str | None = None
    config_version: str = "prototype-2026-09-07"
    calculation_version: str = "engine-0.1.0"
    exclude_outliers: bool = False  # flag_only by default


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class IndexEngine:
    """Configurable index calculation engine.

    Per STATISTICAL_METHODOLOGY.md:
    - Representative fare = median (configurable) of eligible fares per cell
    - Price relative = current / base × 100
    - Composite = Σ(weight × price_relative) for eligible routes
    """

    def __init__(self, config: EngineConfig | None = None):
        self.config = config or EngineConfig()

    def _compute_representative_fare(
        self,
        fares: list[Decimal],
    ) -> Decimal | None:
        """Compute the representative fare from a list of eligible fares."""
        if not fares:
            return None

        float_fares = [float(f) for f in fares]

        if self.config.representative_fare_statistic == "median":
            result = statistics.median(float_fares)
        elif self.config.representative_fare_statistic == "mean":
            result = statistics.mean(float_fares)
        elif self.config.representative_fare_statistic == "trimmed_mean":
            # 10% trimmed mean
            if len(float_fares) >= 10:
                trim = max(1, len(float_fares) // 10)
                sorted_fares = sorted(float_fares)
                result = statistics.mean(sorted_fares[trim:-trim])
            else:
                result = statistics.median(float_fares)
        else:
            result = statistics.median(float_fares)

        return Decimal(str(round(result, 2)))

    def _filter_eligible(
        self,
        observations: list[QualityScoredObservation],
    ) -> tuple[list[Decimal], int]:
        """Filter to eligible fares and count exclusions.

        Eligibility:
          - availability_status == AVAILABLE
          - total_payable_fare is not None and > 0
          - quality_status != INVALID
          - If exclude_outliers, skip outlier-flagged observations

        Returns:
            Tuple of (eligible_fares, excluded_count).
        """
        eligible: list[Decimal] = []
        excluded = 0

        for scored in observations:
            obs = scored.observation

            # Must be available with a valid price
            if obs.availability_status != AvailabilityStatus.AVAILABLE:
                continue
            if obs.total_payable_fare is None or obs.total_payable_fare <= 0:
                continue
            if obs.quality_status == QualityStatus.INVALID:
                excluded += 1
                continue
            if self.config.exclude_outliers and scored.is_outlier:
                excluded += 1
                continue

            eligible.append(obs.total_payable_fare)

        return eligible, excluded

    def compute_daily(
        self,
        observation_date: date,
        observations: list[QualityScoredObservation],
        route_weights: dict[str, float],
        base_fares: dict[str, Decimal] | None = None,
    ) -> IndexResult:
        """Compute the daily index value.

        Args:
            observation_date: The date for this index calculation.
            observations: Quality-scored observations for this date.
            route_weights: Dict of route_code → weight (must sum to ~1.0).
            base_fares: Dict of route_code → base-period representative fare.
                        If None, uses current fares as base (index = 100).

        Returns:
            IndexResult with composite index value and per-route breakdowns.
        """
        # Group observations by route
        route_obs: dict[str, list[QualityScoredObservation]] = defaultdict(list)
        for scored in observations:
            obs = scored.observation
            route_key = f"{obs.origin_airport}-{obs.destination_airport}"
            route_obs[route_key].append(scored)

        route_results: list[RouteIndexResult] = []
        total_obs = 0
        eligible_routes = 0

        for route_code, weight in route_weights.items():
            obs_for_route = route_obs.get(route_code, [])
            eligible_fares, excluded = self._filter_eligible(obs_for_route)

            # Check minimum cell observations
            if len(eligible_fares) < self.config.minimum_cell_observations:
                route_results.append(RouteIndexResult(
                    route_code=route_code,
                    representative_fare=None,
                    base_fare=None,
                    price_relative=None,
                    weight=weight,
                    weighted_contribution=None,
                    observation_count=len(obs_for_route),
                    excluded_count=excluded,
                    is_eligible=False,
                    ineligibility_reason=(
                        f"Insufficient observations: {len(eligible_fares)} < "
                        f"{self.config.minimum_cell_observations}"
                    ),
                ))
                continue

            rep_fare = self._compute_representative_fare(eligible_fares)
            total_obs += len(obs_for_route)

            # Compute price relative
            base_fare = None
            price_relative = None
            weighted_contribution = None

            if base_fares and route_code in base_fares:
                base_fare = base_fares[route_code]
            elif rep_fare is not None:
                # Self-referencing base period: index = 100
                base_fare = rep_fare

            if rep_fare is not None and base_fare is not None and base_fare > 0:
                price_relative = (rep_fare / base_fare * Decimal("100")).quantize(
                    Decimal("0.0001"), rounding=ROUND_HALF_UP
                )
                weighted_contribution = (
                    price_relative * Decimal(str(weight))
                ).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

            if price_relative is not None:
                eligible_routes += 1

            # Cell-level detail
            cell = CellResult(
                route_code=route_code,
                origin=route_code.split("-")[0] if "-" in route_code else "",
                destination=route_code.split("-")[1] if "-" in route_code else "",
                period_start=observation_date,
                period_end=observation_date,
                advance_days=None,
                observation_count=len(eligible_fares),
                excluded_count=excluded,
                representative_fare=rep_fare,
                statistic_used=self.config.representative_fare_statistic,
            )

            route_results.append(RouteIndexResult(
                route_code=route_code,
                representative_fare=rep_fare,
                base_fare=base_fare,
                price_relative=price_relative,
                weight=weight,
                weighted_contribution=weighted_contribution,
                observation_count=len(obs_for_route),
                excluded_count=excluded,
                cells=[cell],
            ))

        # Composite index value
        contributions = [
            rr.weighted_contribution
            for rr in route_results
            if rr.weighted_contribution is not None
        ]

        index_value: Decimal | None = None
        if contributions:
            # Normalize by eligible weight sum
            eligible_weight = sum(
                Decimal(str(rr.weight))
                for rr in route_results
                if rr.weighted_contribution is not None
            )
            raw_sum = sum(contributions)
            if eligible_weight > 0:
                index_value = (raw_sum / eligible_weight).quantize(
                    Decimal("0.0001"), rounding=ROUND_HALF_UP
                )

        coverage = Decimal("0.00")
        if route_weights:
            coverage = Decimal(str(
                round(eligible_routes / len(route_weights) * 100, 2)
            ))

        return IndexResult(
            frequency=IndexFrequency.DAILY.value,
            period_start=observation_date,
            period_end=observation_date,
            index_value=index_value,
            base_period=self.config.base_period,
            config_version=self.config.config_version,
            calculation_version=self.config.calculation_version,
            coverage_pct=coverage,
            route_count=len(route_weights),
            eligible_route_count=eligible_routes,
            observation_count=total_obs,
            route_results=route_results,
        )

    def compute_weekly(
        self,
        week_start: date,
        daily_results: list[IndexResult],
    ) -> IndexResult:
        """Aggregate daily index values into a weekly index.

        Uses the mean of eligible daily values within the week.
        """
        week_end = week_start + timedelta(days=6)
        eligible_dailies = [
            r for r in daily_results
            if (r.index_value is not None
                and week_start <= r.period_start <= week_end)
        ]

        if not eligible_dailies:
            return IndexResult(
                frequency=IndexFrequency.WEEKLY.value,
                period_start=week_start,
                period_end=week_end,
                index_value=None,
                base_period=self.config.base_period,
                config_version=self.config.config_version,
                calculation_version=self.config.calculation_version,
                coverage_pct=Decimal("0.00"),
                route_count=0,
                eligible_route_count=0,
                observation_count=0,
            )

        values = [float(r.index_value) for r in eligible_dailies]  # type: ignore
        weekly_value = Decimal(str(round(statistics.mean(values), 4)))
        total_obs = sum(r.observation_count for r in eligible_dailies)

        return IndexResult(
            frequency=IndexFrequency.WEEKLY.value,
            period_start=week_start,
            period_end=week_end,
            index_value=weekly_value,
            base_period=self.config.base_period,
            config_version=self.config.config_version,
            calculation_version=self.config.calculation_version,
            coverage_pct=Decimal(str(
                round(len(eligible_dailies) / 7 * 100, 2)
            )),
            route_count=eligible_dailies[0].route_count if eligible_dailies else 0,
            eligible_route_count=eligible_dailies[0].eligible_route_count if eligible_dailies else 0,
            observation_count=total_obs,
        )

    def compute_monthly(
        self,
        year: int,
        month: int,
        daily_results: list[IndexResult],
    ) -> IndexResult:
        """Aggregate daily index values into a monthly index.

        Uses the mean of eligible daily values within the month.
        """
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month + 1, 1) - timedelta(days=1)

        eligible_dailies = [
            r for r in daily_results
            if (r.index_value is not None
                and month_start <= r.period_start <= month_end)
        ]

        days_in_month = (month_end - month_start).days + 1

        if not eligible_dailies:
            return IndexResult(
                frequency=IndexFrequency.MONTHLY.value,
                period_start=month_start,
                period_end=month_end,
                index_value=None,
                base_period=self.config.base_period,
                config_version=self.config.config_version,
                calculation_version=self.config.calculation_version,
                coverage_pct=Decimal("0.00"),
                route_count=0,
                eligible_route_count=0,
                observation_count=0,
            )

        values = [float(r.index_value) for r in eligible_dailies]  # type: ignore
        monthly_value = Decimal(str(round(statistics.mean(values), 4)))
        total_obs = sum(r.observation_count for r in eligible_dailies)

        return IndexResult(
            frequency=IndexFrequency.MONTHLY.value,
            period_start=month_start,
            period_end=month_end,
            index_value=monthly_value,
            base_period=self.config.base_period,
            config_version=self.config.config_version,
            calculation_version=self.config.calculation_version,
            coverage_pct=Decimal(str(
                round(len(eligible_dailies) / days_in_month * 100, 2)
            )),
            route_count=eligible_dailies[0].route_count if eligible_dailies else 0,
            eligible_route_count=eligible_dailies[0].eligible_route_count if eligible_dailies else 0,
            observation_count=total_obs,
        )
