"""
Tests for the index calculation engine (Phase 5).

Verifies:
  - Representative fare computation (median, mean, trimmed_mean)
  - Price relative calculation
  - Weighted aggregation into composite index
  - Daily/weekly/monthly index computation
  - Coverage and eligibility handling
  - Self-referencing base period (index = 100)
  - End-to-end: mock generator → pipeline → index engine
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.core.enums import (
    AvailabilityStatus,
    CancellationStatus,
    FareClass,
    QualityStatus,
    SourceType,
)
from app.schemas.domain import FareComponent, FareObservation
from app.services.pipeline import FarePipeline, QualityScoredObservation
from app.index_engine.engine import EngineConfig, IndexEngine


# ===================================================================
# Helpers
# ===================================================================


def _make_scored(
    total_fare: Decimal | None = Decimal("5000.00"),
    origin: str = "DEL",
    destination: str = "BOM",
    availability: AvailabilityStatus = AvailabilityStatus.AVAILABLE,
    quality_status: QualityStatus = QualityStatus.VALID,
    is_outlier: bool = False,
    obs_date: date | None = None,
) -> QualityScoredObservation:
    """Create a quality-scored observation for testing."""
    _date = obs_date or date(2026, 9, 14)

    components = FareComponent()
    if total_fare and availability == AvailabilityStatus.AVAILABLE:
        components = FareComponent(
            base_fare=total_fare * Decimal("0.65"),
            taxes=total_fare * Decimal("0.10"),
        )

    obs = FareObservation(
        observation_id=uuid.uuid4(),
        observed_at=datetime.combine(_date, datetime.min.time(), tzinfo=timezone.utc),
        source_code="MOCK_AIRLINE",
        source_type=SourceType.MOCK,
        origin_airport=origin,
        destination_airport=destination,
        origin_city=origin,
        destination_city=destination,
        departure_date=_date + timedelta(days=7),
        airline_code="6E",
        airline_name="IndiGo",
        fare_class=FareClass.ECONOMY,
        advance_purchase_days=7,
        components=components,
        total_payable_fare=total_fare,
        currency="INR",
        availability_status=availability,
        cancellation_status=CancellationStatus.ACTIVE,
        quality_status=quality_status,
    )

    return QualityScoredObservation(
        observation=obs,
        quality_score=Decimal("90.00"),
        is_outlier=is_outlier,
    )


ROUTE_WEIGHTS = {
    "DEL-BOM": 0.5,
    "BLR-HYD": 0.5,
}


# ===================================================================
# Representative fare
# ===================================================================


class TestRepresentativeFare:
    def test_median_of_odd_count(self):
        engine = IndexEngine(EngineConfig(representative_fare_statistic="median"))
        result = engine._compute_representative_fare([
            Decimal("3000"), Decimal("5000"), Decimal("7000"),
        ])
        assert result == Decimal("5000.00")

    def test_median_of_even_count(self):
        engine = IndexEngine(EngineConfig(representative_fare_statistic="median"))
        result = engine._compute_representative_fare([
            Decimal("3000"), Decimal("4000"), Decimal("5000"), Decimal("6000"),
        ])
        assert result == Decimal("4500.00")

    def test_mean(self):
        engine = IndexEngine(EngineConfig(representative_fare_statistic="mean"))
        result = engine._compute_representative_fare([
            Decimal("3000"), Decimal("5000"), Decimal("7000"),
        ])
        assert result is not None
        assert abs(result - Decimal("5000.00")) < Decimal("1")

    def test_empty_returns_none(self):
        engine = IndexEngine()
        result = engine._compute_representative_fare([])
        assert result is None


# ===================================================================
# Daily index
# ===================================================================


class TestDailyIndex:
    def test_self_referencing_base_index_100(self):
        """Without explicit base fares, index should be 100."""
        engine = IndexEngine()

        obs = [
            _make_scored(Decimal("5000.00"), "DEL", "BOM"),
            _make_scored(Decimal("5200.00"), "DEL", "BOM"),
            _make_scored(Decimal("3000.00"), "BLR", "HYD"),
            _make_scored(Decimal("3200.00"), "BLR", "HYD"),
        ]

        result = engine.compute_daily(date(2026, 9, 14), obs, ROUTE_WEIGHTS)

        assert result.index_value is not None
        assert result.index_value == Decimal("100.0000")
        assert result.coverage_pct == Decimal("100.00")

    def test_index_with_explicit_base(self):
        """With a lower base fare, index should be > 100 (prices increased)."""
        engine = IndexEngine()

        obs = [
            _make_scored(Decimal("6000.00"), "DEL", "BOM"),
            _make_scored(Decimal("3600.00"), "BLR", "HYD"),
        ]

        base_fares = {
            "DEL-BOM": Decimal("5000.00"),
            "BLR-HYD": Decimal("3000.00"),
        }

        result = engine.compute_daily(date(2026, 9, 14), obs, ROUTE_WEIGHTS, base_fares)

        assert result.index_value is not None
        assert result.index_value > Decimal("100")

    def test_index_with_lower_current_fare(self):
        """With higher base fare, index should be < 100 (prices decreased)."""
        engine = IndexEngine()

        obs = [
            _make_scored(Decimal("4000.00"), "DEL", "BOM"),
            _make_scored(Decimal("2500.00"), "BLR", "HYD"),
        ]

        base_fares = {
            "DEL-BOM": Decimal("5000.00"),
            "BLR-HYD": Decimal("3000.00"),
        }

        result = engine.compute_daily(date(2026, 9, 14), obs, ROUTE_WEIGHTS, base_fares)

        assert result.index_value is not None
        assert result.index_value < Decimal("100")

    def test_insufficient_observations(self):
        """Route with 0 observations should be ineligible."""
        engine = IndexEngine(EngineConfig(minimum_cell_observations=2))

        # Only 1 obs for DEL-BOM, 0 for BLR-HYD
        obs = [_make_scored(Decimal("5000.00"), "DEL", "BOM")]

        result = engine.compute_daily(date(2026, 9, 14), obs, ROUTE_WEIGHTS)

        ineligible = [r for r in result.route_results if not r.is_eligible]
        assert len(ineligible) >= 1

    def test_unavailable_excluded(self):
        """Sold-out observations should not contribute to representative fare."""
        engine = IndexEngine()

        obs = [
            _make_scored(Decimal("5000.00"), "DEL", "BOM"),
            _make_scored(None, "DEL", "BOM", availability=AvailabilityStatus.SOLD_OUT),
        ]

        result = engine.compute_daily(
            date(2026, 9, 14), obs, {"DEL-BOM": 1.0},
        )

        # Only the available observation contributes
        del_bom = [r for r in result.route_results if r.route_code == "DEL-BOM"]
        assert len(del_bom) == 1
        assert del_bom[0].representative_fare == Decimal("5000.00")

    def test_outliers_excluded_when_configured(self):
        """With exclude_outliers=True, outlier-flagged obs are excluded."""
        config = EngineConfig(exclude_outliers=True)
        engine = IndexEngine(config)

        obs = [
            _make_scored(Decimal("5000.00"), "DEL", "BOM", is_outlier=False),
            _make_scored(Decimal("50000.00"), "DEL", "BOM", is_outlier=True),
        ]

        result = engine.compute_daily(
            date(2026, 9, 14), obs, {"DEL-BOM": 1.0},
        )

        del_bom = [r for r in result.route_results if r.route_code == "DEL-BOM"]
        assert del_bom[0].representative_fare == Decimal("5000.00")
        assert del_bom[0].excluded_count == 1

    def test_provenance_fields(self):
        engine = IndexEngine()
        obs = [_make_scored(Decimal("5000.00"), "DEL", "BOM")]
        result = engine.compute_daily(date(2026, 9, 14), obs, {"DEL-BOM": 1.0})

        assert result.frequency == "daily"
        assert result.config_version == "prototype-2026-09-07"
        assert result.calculation_version == "engine-0.1.0"
        assert result.period_start == date(2026, 9, 14)
        assert result.period_end == date(2026, 9, 14)


# ===================================================================
# Weekly index
# ===================================================================


class TestWeeklyIndex:
    def test_weekly_averages_dailies(self):
        engine = IndexEngine()

        dailies = []
        for i in range(7):
            obs = [
                _make_scored(Decimal("5000.00"), "DEL", "BOM",
                             obs_date=date(2026, 9, 14) + timedelta(days=i)),
            ]
            result = engine.compute_daily(
                date(2026, 9, 14) + timedelta(days=i),
                obs, {"DEL-BOM": 1.0},
            )
            dailies.append(result)

        weekly = engine.compute_weekly(date(2026, 9, 14), dailies)

        assert weekly.index_value is not None
        assert weekly.index_value == Decimal("100.0000")
        assert weekly.frequency == "weekly"
        assert weekly.coverage_pct == Decimal("100.0")

    def test_weekly_no_data(self):
        engine = IndexEngine()
        weekly = engine.compute_weekly(date(2026, 9, 14), [])
        assert weekly.index_value is None


# ===================================================================
# Monthly index
# ===================================================================


class TestMonthlyIndex:
    def test_monthly_averages_dailies(self):
        engine = IndexEngine()

        dailies = []
        for i in range(10):  # 10 days of a month
            obs = [
                _make_scored(Decimal("5000.00"), "DEL", "BOM",
                             obs_date=date(2026, 9, 1) + timedelta(days=i)),
            ]
            result = engine.compute_daily(
                date(2026, 9, 1) + timedelta(days=i),
                obs, {"DEL-BOM": 1.0},
            )
            dailies.append(result)

        monthly = engine.compute_monthly(2026, 9, dailies)

        assert monthly.index_value is not None
        assert monthly.frequency == "monthly"
        assert monthly.period_start == date(2026, 9, 1)
        assert monthly.period_end == date(2026, 9, 30)

    def test_monthly_no_data(self):
        engine = IndexEngine()
        monthly = engine.compute_monthly(2026, 9, [])
        assert monthly.index_value is None


# ===================================================================
# End-to-end integration
# ===================================================================


class TestEndToEnd:
    def test_mock_to_pipeline_to_index(self):
        """Full chain: mock generator → pipeline → index engine."""
        from app.services.mock_fare_generator import MockFareGenerator

        # Step 1: Generate mock data
        gen = MockFareGenerator(seed=42)
        routes = [
            {"code": "DEL-BOM", "origin": "DEL", "destination": "BOM"},
            {"code": "BLR-HYD", "origin": "BLR", "destination": "HYD"},
        ]
        airlines = [
            {"code": "6E", "name": "IndiGo"},
            {"code": "AI", "name": "Air India"},
        ]
        observations = gen.generate_day(
            date(2026, 9, 14), routes, airlines, [7, 30],
        )
        assert len(observations) > 0

        # Step 2: Process through pipeline
        pipeline = FarePipeline()
        pipeline_result = pipeline.process(observations)
        assert pipeline_result.total_output > 0

        # Step 3: Compute index
        engine = IndexEngine()
        weights = {"DEL-BOM": 0.5, "BLR-HYD": 0.5}
        index_result = engine.compute_daily(
            date(2026, 9, 14),
            pipeline_result.valid,
            weights,
        )

        # Verify index result
        assert index_result.index_value is not None
        assert index_result.index_value == Decimal("100.0000")  # Self-referencing base
        assert index_result.coverage_pct > Decimal("0")
        assert index_result.route_count == 2
        assert len(index_result.route_results) == 2

        # Each route should have a representative fare
        for rr in index_result.route_results:
            if rr.is_eligible:
                assert rr.representative_fare is not None
                assert rr.representative_fare > 0
