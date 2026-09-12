"""
Tests for the mock fare generator (Phase 3).

Verifies:
  - Deterministic output (same seed → same observations)
  - Correct observation structure and field values
  - Route-specific fare ranges
  - Advance-purchase pricing curves
  - Airline multipliers
  - Sold-out and cancelled observations
  - Fare component decomposition
  - Multi-day generation
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.core.enums import AvailabilityStatus, FareClass, SourceType
from app.services.mock_fare_generator import MockFareGenerator


# ===================================================================
# Fixtures
# ===================================================================

ROUTES = [
    {"code": "DEL-BOM", "origin": "DEL", "destination": "BOM"},
    {"code": "BLR-HYD", "origin": "BLR", "destination": "HYD"},
]

AIRLINES = [
    {"code": "6E", "name": "IndiGo", "active": True},
    {"code": "AI", "name": "Air India", "active": True},
    {"code": "G8", "name": "Go First", "active": False},
]

ADVANCE_DAYS = [1, 7, 15, 30, 45]


@pytest.fixture
def gen():
    return MockFareGenerator(seed=42)


# ===================================================================
# Determinism
# ===================================================================


class TestDeterminism:
    def test_same_seed_same_output(self):
        gen1 = MockFareGenerator(seed=123)
        gen2 = MockFareGenerator(seed=123)

        obs1 = gen1.generate_day(date(2026, 9, 14), ROUTES, AIRLINES, ADVANCE_DAYS)
        obs2 = gen2.generate_day(date(2026, 9, 14), ROUTES, AIRLINES, ADVANCE_DAYS)

        assert len(obs1) == len(obs2)
        for a, b in zip(obs1, obs2):
            assert a.observation_id == b.observation_id
            assert a.total_payable_fare == b.total_payable_fare

    def test_different_seed_different_output(self):
        gen1 = MockFareGenerator(seed=1)
        gen2 = MockFareGenerator(seed=2)

        obs1 = gen1.generate_observation(
            "DEL-BOM", "DEL", "BOM", "6E", "IndiGo", date(2026, 9, 14), 7
        )
        obs2 = gen2.generate_observation(
            "DEL-BOM", "DEL", "BOM", "6E", "IndiGo", date(2026, 9, 14), 7
        )

        # Very unlikely to be equal with different seeds
        assert obs1.total_payable_fare != obs2.total_payable_fare

    def test_repeated_generation_same_instance_is_idempotent(self):
        """Regression: flight counts must not depend on prior calls.

        generate_day previously drew flight counts from a stateful RNG,
        so calling it twice on the same instance (as long-lived API
        services do) produced different data for the same date.
        """
        gen = MockFareGenerator(seed=42)

        obs1 = gen.generate_day(date(2026, 9, 14), ROUTES, AIRLINES, ADVANCE_DAYS)
        obs2 = gen.generate_day(date(2026, 9, 14), ROUTES, AIRLINES, ADVANCE_DAYS)
        # A third call after generating a different day in between.
        gen.generate_day(date(2026, 9, 15), ROUTES, AIRLINES, ADVANCE_DAYS)
        obs3 = gen.generate_day(date(2026, 9, 14), ROUTES, AIRLINES, ADVANCE_DAYS)

        ids1 = [str(o.observation_id) for o in obs1]
        ids2 = [str(o.observation_id) for o in obs2]
        ids3 = [str(o.observation_id) for o in obs3]
        assert ids1 == ids2 == ids3


# ===================================================================
# Observation structure
# ===================================================================


class TestObservationStructure:
    def test_basic_fields(self, gen):
        obs = gen.generate_observation(
            "DEL-BOM", "DEL", "BOM", "6E", "IndiGo", date(2026, 9, 14), 7
        )

        assert obs.source_code == "MOCK_AIRLINE"
        assert obs.source_type == SourceType.MOCK
        assert obs.origin_airport == "DEL"
        assert obs.destination_airport == "BOM"
        assert obs.airline_code == "6E"
        assert obs.airline_name == "IndiGo"
        assert obs.fare_class == FareClass.ECONOMY
        assert obs.currency == "INR"
        assert obs.connector_version == "mock-0.1.0"
        assert obs.parser_version == "mock-0.1.0"

    def test_departure_date(self, gen):
        obs = gen.generate_observation(
            "DEL-BOM", "DEL", "BOM", "6E", "IndiGo", date(2026, 9, 14), 7
        )
        expected_departure = date(2026, 9, 14) + timedelta(days=7)
        assert obs.departure_date == expected_departure

    def test_advance_purchase_days(self, gen):
        obs = gen.generate_observation(
            "DEL-BOM", "DEL", "BOM", "6E", "IndiGo", date(2026, 9, 14), 30
        )
        assert obs.advance_purchase_days == 30

    def test_departure_time_present(self, gen):
        obs = gen.generate_observation(
            "DEL-BOM", "DEL", "BOM", "6E", "IndiGo", date(2026, 9, 14), 7
        )
        assert obs.departure_time is not None
        assert obs.arrival_time is not None
        assert obs.arrival_time > obs.departure_time

    def test_flight_number_format(self, gen):
        obs = gen.generate_observation(
            "DEL-BOM", "DEL", "BOM", "6E", "IndiGo", date(2026, 9, 14), 7
        )
        assert obs.flight_number is not None
        assert obs.flight_number.startswith("6E ")


# ===================================================================
# Pricing
# ===================================================================


class TestPricing:
    def test_available_has_positive_fare(self, gen):
        obs = gen.generate_observation(
            "DEL-BOM", "DEL", "BOM", "6E", "IndiGo", date(2026, 9, 14), 7
        )
        if obs.availability_status == AvailabilityStatus.AVAILABLE:
            assert obs.total_payable_fare is not None
            assert obs.total_payable_fare > 0

    def test_advance_purchase_curve(self, gen):
        """Fares for T+1 should be higher than T+45 on average."""
        fares_t1 = []
        fares_t45 = []
        for i in range(20):
            g = MockFareGenerator(seed=i)
            obs1 = g.generate_observation(
                "DEL-BOM", "DEL", "BOM", "6E", "IndiGo", date(2026, 9, 14), 1
            )
            obs45 = g.generate_observation(
                "DEL-BOM", "DEL", "BOM", "6E", "IndiGo", date(2026, 9, 14), 45
            )
            if obs1.total_payable_fare and obs45.total_payable_fare:
                fares_t1.append(float(obs1.total_payable_fare))
                fares_t45.append(float(obs45.total_payable_fare))

        if fares_t1 and fares_t45:
            avg_t1 = sum(fares_t1) / len(fares_t1)
            avg_t45 = sum(fares_t45) / len(fares_t45)
            assert avg_t1 > avg_t45, (
                f"T+1 avg (₹{avg_t1:.0f}) should be > T+45 avg (₹{avg_t45:.0f})"
            )

    def test_fare_in_reasonable_range(self, gen):
        obs = gen.generate_observation(
            "DEL-BOM", "DEL", "BOM", "6E", "IndiGo", date(2026, 9, 14), 7
        )
        if obs.total_payable_fare:
            # DEL-BOM range: roughly ₹2,000 – ₹15,000 with multipliers
            assert obs.total_payable_fare > Decimal("1000")
            assert obs.total_payable_fare < Decimal("20000")


# ===================================================================
# Fare components
# ===================================================================


class TestFareComponents:
    def test_components_populated_for_available(self, gen):
        obs = gen.generate_observation(
            "DEL-BOM", "DEL", "BOM", "6E", "IndiGo", date(2026, 9, 14), 7
        )
        if obs.availability_status == AvailabilityStatus.AVAILABLE:
            comp = obs.components
            assert comp.base_fare is not None
            assert comp.base_fare > 0
            assert comp.taxes is not None
            assert comp.taxes >= 0

    def test_components_sum_close_to_total(self, gen):
        obs = gen.generate_observation(
            "DEL-BOM", "DEL", "BOM", "6E", "IndiGo", date(2026, 9, 14), 7
        )
        if obs.total_payable_fare and obs.components:
            comp = obs.components
            comp_sum = sum(v for v in [
                comp.base_fare, comp.taxes, comp.airport_charges,
                comp.user_development_fee, comp.convenience_fee, comp.other_charges,
            ] if v is not None)
            # Should be approximately equal (rounding may cause small diffs)
            assert abs(comp_sum - obs.total_payable_fare) < Decimal("2.00")


# ===================================================================
# Availability
# ===================================================================


class TestAvailability:
    def test_unavailable_has_null_price(self):
        """With high sold-out probability, some flights should be unavailable."""
        gen = MockFareGenerator(seed=42, sold_out_probability=0.3, cancelled_probability=0.1)
        observations = gen.generate_day(date(2026, 9, 14), ROUTES, AIRLINES, ADVANCE_DAYS)

        unavailable = [
            o for o in observations
            if o.availability_status != AvailabilityStatus.AVAILABLE
        ]
        # With 40% unavailability, we should see some
        assert len(unavailable) > 0
        for o in unavailable:
            assert o.total_payable_fare is None

    def test_inactive_airlines_excluded(self, gen):
        observations = gen.generate_day(date(2026, 9, 14), ROUTES, AIRLINES, ADVANCE_DAYS)
        airline_codes = {o.airline_code for o in observations}
        # G8 is inactive, should not appear
        assert "G8" not in airline_codes


# ===================================================================
# Batch generation
# ===================================================================


class TestBatchGeneration:
    def test_generate_day_count(self, gen):
        observations = gen.generate_day(date(2026, 9, 14), ROUTES, AIRLINES, ADVANCE_DAYS)
        # 2 routes × 2 active airlines × 5 advance_days × ~3 flights = ~60
        assert len(observations) > 10

    def test_generate_date_range(self, gen):
        observations = gen.generate_date_range(
            date(2026, 9, 14), date(2026, 9, 16),
            ROUTES, AIRLINES, ADVANCE_DAYS,
        )
        # 3 days worth of observations
        assert len(observations) > 30
        obs_dates = {o.observed_at.date() for o in observations}
        assert date(2026, 9, 14) in obs_dates
        assert date(2026, 9, 15) in obs_dates
        assert date(2026, 9, 16) in obs_dates
