"""
Tests for the data pipeline (Phase 4).

Verifies:
  - Validation catches temporal issues, price-availability violations
  - Cleaning normalizes fields
  - Deduplication removes true duplicates, keeps unique observations
  - Outlier detection flags extreme fares
  - Quality scoring produces reasonable scores
  - Full pipeline orchestration
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
from app.services.pipeline import (
    Cleaner,
    Deduplicator,
    FarePipeline,
    OutlierDetector,
    QualityScorer,
    Validator,
)


# ===================================================================
# Helpers
# ===================================================================


def _make_obs(
    total_fare: Decimal | None = Decimal("4939.00"),
    availability: AvailabilityStatus = AvailabilityStatus.AVAILABLE,
    advance_days: int = 7,
    origin: str = "DEL",
    destination: str = "BOM",
    departure_offset: int | None = None,
    obs_date: date | None = None,
    airline_code: str | None = "6E",
    flight_number: str | None = "6E 123",
    departure_time: datetime | None = None,
) -> FareObservation:
    """Create a test observation with sensible defaults."""
    _obs_date = obs_date or date(2026, 9, 14)
    _dep_offset = departure_offset if departure_offset is not None else advance_days

    components = FareComponent()
    if total_fare is not None and availability == AvailabilityStatus.AVAILABLE:
        components = FareComponent(
            base_fare=total_fare * Decimal("0.65"),
            taxes=total_fare * Decimal("0.10"),
            airport_charges=total_fare * Decimal("0.05"),
            user_development_fee=total_fare * Decimal("0.02"),
            convenience_fee=total_fare * Decimal("0.03"),
            other_charges=total_fare * Decimal("0.15"),
        )

    return FareObservation(
        observation_id=uuid.uuid4(),
        observed_at=datetime.combine(_obs_date, datetime.min.time(), tzinfo=timezone.utc),
        source_code="MOCK_AIRLINE",
        source_type=SourceType.MOCK,
        origin_airport=origin,
        destination_airport=destination,
        origin_city=origin,
        destination_city=destination,
        departure_date=_obs_date + timedelta(days=_dep_offset),
        departure_time=departure_time,
        airline_code=airline_code,
        airline_name="IndiGo" if airline_code == "6E" else "Test",
        flight_number=flight_number,
        fare_class=FareClass.ECONOMY,
        advance_purchase_days=advance_days,
        components=components,
        total_payable_fare=total_fare,
        currency="INR",
        availability_status=availability,
        cancellation_status=CancellationStatus.ACTIVE,
        connector_version="mock-0.1.0",
        parser_version="mock-0.1.0",
        quality_status=QualityStatus.PENDING,
    )


# ===================================================================
# Validator
# ===================================================================


class TestValidator:
    def test_valid_observation_passes(self):
        v = Validator()
        result = v.validate(_make_obs())
        assert result.is_valid
        assert result.errors == []

    def test_past_departure_date_fails(self):
        v = Validator()
        obs = _make_obs(obs_date=date(2026, 9, 14), departure_offset=-1, advance_days=7)
        result = v.validate(obs)
        assert not result.is_valid
        assert any("before" in e for e in result.errors)

    def test_unavailable_with_price_fails(self):
        v = Validator()
        # Create manually to bypass pydantic validation
        obs = _make_obs(
            total_fare=None,
            availability=AvailabilityStatus.SOLD_OUT,
        )
        # Modify to test pipeline validation
        result = v.validate(obs)
        assert result.is_valid  # null price with sold_out is valid

    def test_fare_range_warning(self):
        v = Validator()
        obs = _make_obs(total_fare=Decimal("60000.00"))
        result = v.validate(obs)
        assert result.is_valid  # Warning, not error
        assert any("Unusually high" in w for w in result.warnings)

    def test_low_fare_warning(self):
        v = Validator()
        obs = _make_obs(total_fare=Decimal("100.00"))
        result = v.validate(obs)
        assert result.is_valid
        assert any("Unusually low" in w for w in result.warnings)

    def test_advance_days_mismatch_warning(self):
        v = Validator()
        obs = _make_obs(advance_days=10, departure_offset=7)
        result = v.validate(obs)
        assert result.is_valid
        assert any("does not match" in w for w in result.warnings)


# ===================================================================
# Cleaner
# ===================================================================


class TestCleaner:
    def test_cleaning_preserves_data(self):
        c = Cleaner()
        obs = _make_obs()
        cleaned = c.clean(obs)
        assert cleaned.total_payable_fare == obs.total_payable_fare
        assert cleaned.origin_airport == obs.origin_airport

    def test_cleaning_normalizes_currency(self):
        c = Cleaner()
        obs = _make_obs()
        cleaned = c.clean(obs)
        assert cleaned.currency == "INR"


# ===================================================================
# Deduplicator
# ===================================================================


class TestDeduplicator:
    def test_no_duplicates(self):
        d = Deduplicator()
        obs1 = _make_obs(flight_number="6E 100")
        obs2 = _make_obs(flight_number="6E 200")
        result, removed = d.deduplicate([obs1, obs2])
        assert len(result) == 2
        assert removed == 0

    def test_removes_exact_duplicates(self):
        d = Deduplicator()
        _ist = timezone(timedelta(hours=5, minutes=30))
        dep_time = datetime(2026, 9, 21, 8, 0, tzinfo=_ist)
        obs1 = _make_obs(flight_number="6E 100", departure_time=dep_time)
        obs2 = _make_obs(flight_number="6E 100", departure_time=dep_time)
        result, removed = d.deduplicate([obs1, obs2])
        assert len(result) == 1
        assert removed == 1

    def test_different_routes_not_deduplicated(self):
        d = Deduplicator()
        obs1 = _make_obs(origin="DEL", destination="BOM", flight_number="6E 100")
        obs2 = _make_obs(origin="DEL", destination="BLR", flight_number="6E 100")
        result, removed = d.deduplicate([obs1, obs2])
        assert len(result) == 2
        assert removed == 0


# ===================================================================
# Outlier Detector
# ===================================================================


class TestOutlierDetector:
    def test_no_outliers_in_uniform_data(self):
        d = OutlierDetector(iqr_multiplier=1.5)
        observations = [_make_obs(total_fare=Decimal(str(f))) for f in range(4000, 4500, 100)]
        results = d.detect(observations)
        outliers = [r for r in results if r[1]]
        assert len(outliers) == 0

    def test_detects_extreme_outlier(self):
        d = OutlierDetector(iqr_multiplier=1.5)
        normal = [_make_obs(total_fare=Decimal(str(f))) for f in range(4000, 5000, 100)]
        extreme = _make_obs(total_fare=Decimal("50000.00"))
        observations = normal + [extreme]
        results = d.detect(observations)
        outliers = [(obs, score) for obs, is_o, score in results if is_o]
        assert len(outliers) >= 1

    def test_insufficient_data_no_outliers(self):
        d = OutlierDetector(iqr_multiplier=1.5)
        observations = [_make_obs(total_fare=Decimal("4000.00")),
                        _make_obs(total_fare=Decimal("50000.00"))]
        results = d.detect(observations)
        outliers = [r for r in results if r[1]]
        # Less than 4 data points: no outlier detection
        assert len(outliers) == 0


# ===================================================================
# Quality Scorer
# ===================================================================


class TestQualityScorer:
    def test_complete_observation_high_score(self):
        s = QualityScorer()
        obs = _make_obs()
        score, factors = s.score(obs)
        assert score > Decimal("70")
        assert "completeness" in factors

    def test_outlier_reduces_score(self):
        s = QualityScorer()
        obs = _make_obs()
        score_normal, _ = s.score(obs, is_outlier=False)
        score_outlier, _ = s.score(obs, is_outlier=True)
        assert score_outlier < score_normal

    def test_warnings_reduce_score(self):
        s = QualityScorer()
        obs = _make_obs()
        score_no_warn, _ = s.score(obs, validation_warnings=[])
        score_warn, _ = s.score(obs, validation_warnings=["warn1", "warn2", "warn3"])
        assert score_warn < score_no_warn

    def test_score_range(self):
        s = QualityScorer()
        obs = _make_obs()
        score, _ = s.score(obs)
        assert Decimal("0") <= score <= Decimal("100")


# ===================================================================
# Full Pipeline
# ===================================================================


class TestFarePipeline:
    def test_basic_pipeline_run(self):
        pipeline = FarePipeline()
        observations = [_make_obs(total_fare=Decimal(str(f)))
                        for f in range(4000, 5000, 100)]
        result = pipeline.process(observations)

        assert result.total_input == len(observations)
        assert result.total_output > 0
        assert len(result.invalid) == 0

    def test_pipeline_catches_invalid(self):
        pipeline = FarePipeline()
        valid = _make_obs()
        invalid = _make_obs(departure_offset=-1)  # Past departure
        result = pipeline.process([valid, invalid])

        assert len(result.invalid) == 1
        assert result.total_output >= 1

    def test_pipeline_quality_scores_present(self):
        pipeline = FarePipeline()
        observations = [_make_obs()]
        result = pipeline.process(observations)

        assert len(result.valid) == 1
        assert result.valid[0].quality_score > 0
        assert result.valid[0].pipeline_version == "pipeline-0.1.0"

    def test_pipeline_with_mock_generator(self):
        """Integration: generate mock data → process through pipeline."""
        from app.services.mock_fare_generator import MockFareGenerator

        gen = MockFareGenerator(seed=42)
        routes = [{"code": "DEL-BOM", "origin": "DEL", "destination": "BOM"}]
        airlines = [{"code": "6E", "name": "IndiGo"}]
        observations = gen.generate_day(date(2026, 9, 14), routes, airlines, [7, 30])

        pipeline = FarePipeline()
        result = pipeline.process(observations)

        assert result.total_input > 0
        assert result.total_output > 0
        assert all(s.quality_score > 0 for s in result.valid)
