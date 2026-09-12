"""
Deterministic mock airfare generator for AirIndex India.

Produces realistic synthetic fare observations for development, testing,
and demonstration. Uses seeded randomness so results are reproducible.

Features:
  - Route-specific base fare ranges (calibrated to real Indian domestic fare levels)
  - Airline-specific fare multipliers (budget vs full-service)
  - Advance-purchase pricing curves (fares increase as departure approaches)
  - Time-of-day / day-of-week variation
  - Configurable sold-out / cancelled probability
  - Fare component decomposition (base fare, taxes, charges, UDF, convenience)
  - Deterministic when seeded

Status: DEMO / PROTOTYPE / ASSUMPTION — not real market data.

Usage:
    from app.services.mock_fare_generator import MockFareGenerator
    gen = MockFareGenerator(seed=42)
    observations = gen.generate_day(
        observation_date=date(2026, 9, 14),
        routes=[...],
        airlines=[...],
        advance_days=[1, 7, 15, 30, 45],
    )
"""

from __future__ import annotations

import hashlib
import random
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from app.core.enums import (
    AvailabilityStatus,
    CancellationStatus,
    FareClass,
    QualityStatus,
    SourceType,
)
from app.schemas.domain import FareComponent, FareObservation


# ---------------------------------------------------------------------------
# Route fare profiles (calibrated to INR domestic fare ranges)
# ---------------------------------------------------------------------------

# Base fare range (INR) by route distance tier
_ROUTE_BASE_FARES: dict[str, tuple[float, float]] = {
    # Short-haul (~1–2 hrs)
    "BLR-HYD": (2800, 5500),
    "BOM-GOI": (2500, 5000),
    "DEL-JAI": (2200, 4500),
    "BOM-PNQ": (2400, 4800),
    # Medium-haul (~2–3 hrs)
    "DEL-BOM": (3500, 8500),
    "DEL-BLR": (3800, 9000),
    "BOM-BLR": (3200, 7500),
    "DEL-CCU": (3500, 8000),
    "MAA-DEL": (3600, 8500),
    "DEL-HYD": (3200, 7500),
    "BOM-CCU": (4000, 9000),
    "BLR-CCU": (4200, 9500),
    # Long-haul (~3+ hrs)
    "DEL-MAA": (3800, 9000),
    "DEL-COK": (4200, 10000),
    "BOM-GAU": (5000, 11000),
}

# Airline fare multiplier (budget carriers cheaper, full-service premium)
_AIRLINE_MULTIPLIER: dict[str, float] = {
    "6E": 0.92,   # IndiGo — budget king
    "SG": 0.95,   # SpiceJet — budget
    "QP": 0.94,   # Akasa — new budget
    "I5": 0.93,   # AirAsia India — budget
    "G8": 0.96,   # Go First — budget (inactive but generating history)
    "IX": 0.97,   # Air India Express — hybrid
    "AI": 1.12,   # Air India — full service
    "UK": 1.08,   # Vistara — full service
}

_DEFAULT_MULTIPLIER = 1.0


# ---------------------------------------------------------------------------
# Advance-purchase pricing curve
# ---------------------------------------------------------------------------

def _advance_purchase_factor(days: int) -> float:
    """Fare multiplier based on days-before-departure.

    Mimics real pricing: fares are lowest 30-45 days out, increase
    sharply within 7 days, and peak at T+1.
    """
    if days >= 45:
        return 0.75
    elif days >= 30:
        return 0.82
    elif days >= 15:
        return 0.93
    elif days >= 7:
        return 1.05
    elif days >= 3:
        return 1.25
    elif days >= 1:
        return 1.45
    else:
        return 1.60


# ---------------------------------------------------------------------------
# Fare component decomposition
# ---------------------------------------------------------------------------

def _decompose_fare(total: Decimal, rng: random.Random) -> FareComponent:
    """Split total fare into realistic Indian domestic components.

    Typical breakdown:
      Base fare: ~60-70%
      Taxes (GST): ~5-12%
      Airport charges (PSF+DF): ~3-6%
      UDF: ~1-3%
      Convenience fee: ~2-5%
      Other charges: ~0-2%
    """
    base_pct = Decimal(str(rng.uniform(0.60, 0.70)))
    tax_pct = Decimal(str(rng.uniform(0.05, 0.12)))
    airport_pct = Decimal(str(rng.uniform(0.03, 0.06)))
    udf_pct = Decimal(str(rng.uniform(0.01, 0.03)))
    conv_pct = Decimal(str(rng.uniform(0.02, 0.05)))

    base_fare = (total * base_pct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    taxes = (total * tax_pct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    airport_charges = (total * airport_pct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    udf = (total * udf_pct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    conv = (total * conv_pct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    other = total - base_fare - taxes - airport_charges - udf - conv
    if other < 0:
        other = Decimal("0.00")

    return FareComponent(
        base_fare=base_fare,
        taxes=taxes,
        airport_charges=airport_charges,
        user_development_fee=udf,
        convenience_fee=conv,
        other_charges=other,
    )


# ---------------------------------------------------------------------------
# Departure time generation
# ---------------------------------------------------------------------------

_DEPARTURE_SLOTS = [
    time(6, 0), time(6, 30), time(7, 0), time(7, 30),
    time(8, 0), time(8, 30), time(9, 0), time(9, 30),
    time(10, 0), time(11, 0), time(12, 0),
    time(13, 0), time(14, 0), time(15, 0),
    time(16, 0), time(17, 0), time(18, 0),
    time(19, 0), time(20, 0), time(21, 0), time(22, 0),
]

_IST = timezone(timedelta(hours=5, minutes=30))


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

@dataclass
class MockFareGenerator:
    """Deterministic mock fare observation generator.

    Args:
        seed: Random seed for reproducibility.
        sold_out_probability: Chance a flight is sold out (0-1).
        cancelled_probability: Chance a flight is cancelled (0-1).
        flights_per_route_airline: Typical number of daily flights per route-airline pair.
    """

    seed: int = 42
    sold_out_probability: float = 0.05
    cancelled_probability: float = 0.02
    flights_per_route_airline: int = 3
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._rng = random.Random(self.seed)

    def _route_seed(self, route_code: str, airline_code: str,
                    obs_date: date, advance_days: int, flight_idx: int) -> int:
        """Create a deterministic sub-seed for a specific observation."""
        key = f"{self.seed}:{route_code}:{airline_code}:{obs_date}:{advance_days}:{flight_idx}"
        return int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)

    def _get_base_range(self, route_code: str) -> tuple[float, float]:
        """Look up base fare range, falling back to a sensible default."""
        if route_code in _ROUTE_BASE_FARES:
            return _ROUTE_BASE_FARES[route_code]
        # Try reversed route code
        parts = route_code.split("-")
        if len(parts) == 2:
            rev = f"{parts[1]}-{parts[0]}"
            if rev in _ROUTE_BASE_FARES:
                return _ROUTE_BASE_FARES[rev]
        return (3000, 7500)  # Default domestic range

    def generate_observation(
        self,
        route_code: str,
        origin: str,
        destination: str,
        airline_code: str,
        airline_name: str,
        observation_date: date,
        advance_days: int,
        flight_idx: int = 0,
    ) -> FareObservation:
        """Generate a single mock fare observation.

        Deterministic given the same generator seed and input parameters.
        """
        sub_seed = self._route_seed(route_code, airline_code, observation_date, advance_days, flight_idx)
        rng = random.Random(sub_seed)

        departure_date = observation_date + timedelta(days=advance_days)
        observed_at = datetime.combine(
            observation_date,
            time(rng.randint(5, 10), rng.randint(0, 59)),
            tzinfo=timezone.utc,
        )

        # Determine availability
        avail_roll = rng.random()
        if avail_roll < self.cancelled_probability:
            availability = AvailabilityStatus.CANCELLED
            cancellation = CancellationStatus.CANCELLED
        elif avail_roll < self.cancelled_probability + self.sold_out_probability:
            availability = AvailabilityStatus.SOLD_OUT
            cancellation = CancellationStatus.ACTIVE
        else:
            availability = AvailabilityStatus.AVAILABLE
            cancellation = CancellationStatus.ACTIVE

        # Departure/arrival times
        dep_slot = rng.choice(_DEPARTURE_SLOTS)
        dep_time = datetime.combine(departure_date, dep_slot, tzinfo=_IST)
        flight_duration_mins = rng.randint(90, 210)
        arr_time = dep_time + timedelta(minutes=flight_duration_mins)

        # Flight number
        flight_num = f"{airline_code} {rng.randint(100, 999)}"

        # Price calculation (only for available flights)
        total_payable: Optional[Decimal] = None
        components = FareComponent()

        if availability == AvailabilityStatus.AVAILABLE:
            lo, hi = self._get_base_range(route_code)
            base = rng.uniform(lo, hi)

            # Apply multipliers
            airline_mult = _AIRLINE_MULTIPLIER.get(airline_code, _DEFAULT_MULTIPLIER)
            advance_mult = _advance_purchase_factor(advance_days)

            # Day-of-week variation (weekday premium)
            dow = departure_date.weekday()
            if dow in (4, 6):  # Fri, Sun
                dow_mult = 1.08
            elif dow == 5:  # Sat
                dow_mult = 0.95
            else:
                dow_mult = 1.0

            # Random noise ±5%
            noise = rng.uniform(0.95, 1.05)

            total = base * airline_mult * advance_mult * dow_mult * noise
            total_payable = Decimal(str(round(total, 2)))
            components = _decompose_fare(total_payable, rng)

        return FareObservation(
            observation_id=uuid.UUID(int=sub_seed),
            observed_at=observed_at,
            source_code="MOCK_AIRLINE",
            source_type=SourceType.MOCK,
            origin_airport=origin,
            destination_airport=destination,
            origin_city=origin,  # Simplified; full lookup in pipeline
            destination_city=destination,
            departure_date=departure_date,
            departure_time=dep_time,
            arrival_time=arr_time,
            airline_code=airline_code,
            airline_name=airline_name,
            flight_number=flight_num,
            fare_class=FareClass.ECONOMY,
            advance_purchase_days=advance_days,
            components=components,
            total_payable_fare=total_payable,
            currency="INR",
            availability_status=availability,
            cancellation_status=cancellation,
            connector_version="mock-0.1.0",
            parser_version="mock-0.1.0",
            quality_status=QualityStatus.PENDING,
        )

    def generate_day(
        self,
        observation_date: date,
        routes: list[dict],
        airlines: list[dict],
        advance_days: list[int],
    ) -> list[FareObservation]:
        """Generate all observations for a single day.

        Args:
            observation_date: The collection date.
            routes: List of dicts with keys: code, origin, destination.
            airlines: List of dicts with keys: code, name, active.
            advance_days: List of advance-purchase day windows.

        Returns:
            List of FareObservation objects.
        """
        observations: list[FareObservation] = []
        active_airlines = [a for a in airlines if a.get("active", True)]

        for route in routes:
            for airline in active_airlines:
                for adv in advance_days:
                    # Deterministic flight count per (route, airline, date,
                    # window) so repeated generation of the same day is
                    # idempotent regardless of prior calls on this instance.
                    count_key = (
                        f"{self.seed}:count:{route['code']}:{airline['code']}"
                        f":{observation_date}:{adv}"
                    )
                    count_seed = int(
                        hashlib.sha256(count_key.encode()).hexdigest()[:8], 16
                    )
                    count_rng = random.Random(count_seed)
                    n_flights = max(1, count_rng.randint(
                        self.flights_per_route_airline - 1,
                        self.flights_per_route_airline + 1,
                    ))
                    for fi in range(n_flights):
                        obs = self.generate_observation(
                            route_code=route["code"],
                            origin=route["origin"],
                            destination=route["destination"],
                            airline_code=airline["code"],
                            airline_name=airline["name"],
                            observation_date=observation_date,
                            advance_days=adv,
                            flight_idx=fi,
                        )
                        observations.append(obs)
        return observations

    def generate_date_range(
        self,
        start_date: date,
        end_date: date,
        routes: list[dict],
        airlines: list[dict],
        advance_days: list[int],
    ) -> list[FareObservation]:
        """Generate observations for a date range (inclusive).

        Returns:
            List of FareObservation objects.
        """
        all_obs: list[FareObservation] = []
        current = start_date
        while current <= end_date:
            day_obs = self.generate_day(current, routes, airlines, advance_days)
            all_obs.extend(day_obs)
            current += timedelta(days=1)
        return all_obs
