"""
Tests for Pydantic domain models.

Covers valid construction, field-level validation, cross-field invariants,
and expected rejection of invalid inputs.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.core.enums import (
    AvailabilityStatus,
    CancellationStatus,
    ComplianceStatus,
    ConfigStatus,
    FareClass,
    IndexFrequency,
    MissingCellPolicy,
    OutlierPolicy,
    QualityStatus,
    SourceType,
    WeightRedistributionPolicy,
)
from app.schemas.domain import (
    AdvanceWindowConfig,
    Airline,
    AirlineConfig,
    Airport,
    AirportConfig,
    FareComponent,
    FareObservation,
    IndexConfig,
    Route,
    RouteConfig,
    Source,
    SourceConfig,
)


# ===================================================================
# Airport
# ===================================================================


class TestAirport:
    def test_valid(self):
        a = Airport(
            iata_code="DEL",
            name="Indira Gandhi International Airport",
            city_code="DEL",
            city_name="Delhi",
        )
        assert a.iata_code == "DEL"
        assert a.active is True  # default

    def test_lowercased_input_normalized(self):
        a = Airport(iata_code="del", name="Test", city_code="del", city_name="Delhi")
        assert a.iata_code == "DEL"
        assert a.city_code == "DEL"

    def test_invalid_iata_too_short(self):
        with pytest.raises(ValidationError, match="3 uppercase letters"):
            Airport(iata_code="DE", name="Test", city_code="DEL", city_name="Delhi")

    def test_invalid_iata_with_digits(self):
        with pytest.raises(ValidationError, match="3 uppercase letters"):
            Airport(iata_code="D3L", name="Test", city_code="DEL", city_name="Delhi")

    def test_frozen(self):
        a = Airport(iata_code="BOM", name="Test", city_code="BOM", city_name="Mumbai")
        with pytest.raises(ValidationError):
            a.iata_code = "DEL"


# ===================================================================
# Airline
# ===================================================================


class TestAirline:
    def test_valid_two_char(self):
        a = Airline(code="6E", name="IndiGo")
        assert a.code == "6E"

    def test_valid_three_char(self):
        a = Airline(code="IGO", name="IndiGo")
        assert a.code == "IGO"

    def test_lowercased_normalized(self):
        a = Airline(code="ai", name="Air India")
        assert a.code == "AI"

    def test_invalid_single_char(self):
        with pytest.raises(ValidationError, match="2–3 uppercase alphanumeric"):
            Airline(code="A", name="Test")

    def test_invalid_four_chars(self):
        with pytest.raises(ValidationError, match="2–3 uppercase alphanumeric"):
            Airline(code="ABCD", name="Test")


# ===================================================================
# Route
# ===================================================================


class TestRoute:
    def _make(self, **overrides):
        defaults = dict(
            code="DEL-BOM",
            origin="DEL",
            destination="BOM",
            weight=0.5,
            effective_from=date(2026, 1, 1),
        )
        defaults.update(overrides)
        return Route(**defaults)

    def test_valid(self):
        r = self._make()
        assert r.origin == "DEL"
        assert r.effective_to is None

    def test_origin_equals_destination_rejected(self):
        with pytest.raises(ValidationError, match="must differ"):
            self._make(origin="DEL", destination="DEL")

    def test_weight_zero_rejected(self):
        with pytest.raises(ValidationError):
            self._make(weight=0)

    def test_weight_above_one_rejected(self):
        with pytest.raises(ValidationError):
            self._make(weight=1.5)

    def test_negative_weight_rejected(self):
        with pytest.raises(ValidationError):
            self._make(weight=-0.1)

    def test_effective_date_order(self):
        with pytest.raises(ValidationError, match="must not precede"):
            self._make(
                effective_from=date(2026, 6, 1),
                effective_to=date(2026, 1, 1),
            )

    def test_airport_code_validated(self):
        with pytest.raises(ValidationError, match="3 uppercase letters"):
            self._make(origin="XX")


# ===================================================================
# Source
# ===================================================================


class TestSource:
    def test_valid(self):
        s = Source(
            code="MOCK_AIRLINE",
            type=SourceType.MOCK,
            enabled=True,
            compliance_status=ComplianceStatus.APPROVED_FOR_SYNTHETIC_DEVELOPMENT,
            rate_limit_per_minute=60,
        )
        assert s.enabled is True

    def test_defaults(self):
        s = Source(code="X", type=SourceType.AIRLINE)
        assert s.enabled is False
        assert s.compliance_status == ComplianceStatus.UNKNOWN
        assert s.rate_limit_per_minute is None

    def test_rate_limit_zero_rejected(self):
        with pytest.raises(ValidationError):
            Source(code="X", type=SourceType.AIRLINE, rate_limit_per_minute=0)


# ===================================================================
# RouteConfig
# ===================================================================


class TestRouteConfig:
    def _routes(self, n: int = 2) -> list[dict]:
        pairs = [("DEL", "BOM"), ("BLR", "HYD"), ("CCU", "MAA"), ("GOI", "PNQ")]
        w = 1.0 / n
        return [
            dict(
                code=f"{o}-{d}",
                origin=o,
                destination=d,
                weight=w,
                effective_from="2026-01-01",
            )
            for o, d in pairs[:n]
        ]

    def test_valid(self):
        rc = RouteConfig(version="v1", routes=self._routes(2))
        assert len(rc.routes) == 2

    def test_weights_must_sum_to_one(self):
        routes = self._routes(2)
        routes[0]["weight"] = 0.3
        routes[1]["weight"] = 0.3
        with pytest.raises(ValidationError, match="sum to"):
            RouteConfig(version="v1", routes=routes)

    def test_duplicate_codes_rejected(self):
        routes = self._routes(2)
        routes[1]["code"] = routes[0]["code"]
        routes[1]["origin"] = "CCU"
        routes[1]["destination"] = "MAA"
        with pytest.raises(ValidationError, match="Duplicate route"):
            RouteConfig(version="v1", routes=routes)

    def test_empty_routes_rejected(self):
        with pytest.raises(ValidationError):
            RouteConfig(version="v1", routes=[])


# ===================================================================
# SourceConfig
# ===================================================================


class TestSourceConfig:
    def test_valid(self):
        sc = SourceConfig(
            version="v1",
            sources=[
                Source(code="A", type=SourceType.MOCK),
                Source(code="B", type=SourceType.AIRLINE),
            ],
        )
        assert len(sc.sources) == 2

    def test_duplicate_sources_rejected(self):
        with pytest.raises(ValidationError, match="Duplicate source"):
            SourceConfig(
                version="v1",
                sources=[
                    Source(code="A", type=SourceType.MOCK),
                    Source(code="A", type=SourceType.AIRLINE),
                ],
            )


# ===================================================================
# AdvanceWindowConfig
# ===================================================================


class TestAdvanceWindowConfig:
    def test_valid(self):
        awc = AdvanceWindowConfig(
            version="v1", advance_purchase_days=[1, 7, 15, 30, 45]
        )
        assert awc.advance_purchase_days == [1, 7, 15, 30, 45]

    def test_auto_sorts(self):
        awc = AdvanceWindowConfig(
            version="v1", advance_purchase_days=[45, 1, 7]
        )
        assert awc.advance_purchase_days == [1, 7, 45]

    def test_zero_rejected(self):
        with pytest.raises(ValidationError, match="positive"):
            AdvanceWindowConfig(version="v1", advance_purchase_days=[0, 1])

    def test_negative_rejected(self):
        with pytest.raises(ValidationError, match="positive"):
            AdvanceWindowConfig(version="v1", advance_purchase_days=[-1])

    def test_duplicates_rejected(self):
        with pytest.raises(ValidationError, match="unique"):
            AdvanceWindowConfig(version="v1", advance_purchase_days=[7, 7])


# ===================================================================
# IndexConfig
# ===================================================================


class TestIndexConfig:
    def test_valid(self):
        ic = IndexConfig(
            version="v1",
            frequencies=[IndexFrequency.DAILY],
        )
        assert ic.currency == "INR"
        assert ic.minimum_cell_observations == 1
        assert ic.outlier_policy == OutlierPolicy.FLAG_ONLY

    def test_bad_currency_rejected(self):
        with pytest.raises(ValidationError, match="ISO 4217"):
            IndexConfig(version="v1", currency="US", frequencies=["daily"])

    def test_min_observations_zero_rejected(self):
        with pytest.raises(ValidationError):
            IndexConfig(version="v1", frequencies=["daily"], minimum_cell_observations=0)


# ===================================================================
# AirportConfig / AirlineConfig
# ===================================================================


class TestAirportConfig:
    def test_duplicate_iata_rejected(self):
        with pytest.raises(ValidationError, match="Duplicate IATA"):
            AirportConfig(
                version="v1",
                airports=[
                    Airport(iata_code="DEL", name="A", city_code="DEL", city_name="Delhi"),
                    Airport(iata_code="DEL", name="B", city_code="DEL", city_name="Delhi"),
                ],
            )


class TestAirlineConfig:
    def test_duplicate_airline_rejected(self):
        with pytest.raises(ValidationError, match="Duplicate airline"):
            AirlineConfig(
                version="v1",
                airlines=[
                    Airline(code="6E", name="IndiGo"),
                    Airline(code="6E", name="IndiGo Duplicate"),
                ],
            )


# ===================================================================
# FareComponent
# ===================================================================


class TestFareComponent:
    def test_valid_all_populated(self):
        fc = FareComponent(
            base_fare=Decimal("4200"),
            taxes=Decimal("310"),
            airport_charges=Decimal("150"),
            user_development_fee=Decimal("80"),
            convenience_fee=Decimal("199"),
            other_charges=Decimal("0"),
        )
        assert fc.base_fare == Decimal("4200")

    def test_all_none_by_default(self):
        fc = FareComponent()
        assert fc.base_fare is None

    def test_negative_rejected(self):
        with pytest.raises(ValidationError):
            FareComponent(base_fare=Decimal("-1"))


# ===================================================================
# FareObservation
# ===================================================================


class TestFareObservation:
    def _make(self, **overrides):
        defaults = dict(
            observed_at=datetime(2026, 9, 7, 6, 30, tzinfo=timezone.utc),
            source_code="MOCK_AIRLINE",
            source_type=SourceType.MOCK,
            origin_airport="DEL",
            destination_airport="BOM",
            origin_city="Delhi",
            destination_city="Mumbai",
            departure_date=date(2026, 9, 14),
            advance_purchase_days=7,
            currency="INR",
            availability_status=AvailabilityStatus.AVAILABLE,
            total_payable_fare=Decimal("4939.00"),
            connector_version="mock-0.1.0",
            parser_version="mock-0.1.0",
        )
        defaults.update(overrides)
        return FareObservation(**defaults)

    def test_valid(self):
        obs = self._make()
        assert obs.origin_airport == "DEL"
        assert obs.quality_status == QualityStatus.PENDING

    def test_origin_equals_destination_rejected(self):
        with pytest.raises(ValidationError, match="must differ"):
            self._make(origin_airport="DEL", destination_airport="DEL")

    def test_negative_advance_days_rejected(self):
        with pytest.raises(ValidationError):
            self._make(advance_purchase_days=-1)

    def test_sold_out_with_price_rejected(self):
        """Non-available observations must not have a payable price."""
        with pytest.raises(ValidationError, match="must be null"):
            self._make(
                availability_status=AvailabilityStatus.SOLD_OUT,
                total_payable_fare=Decimal("1000"),
            )

    def test_sold_out_with_null_price_ok(self):
        obs = self._make(
            availability_status=AvailabilityStatus.SOLD_OUT,
            total_payable_fare=None,
        )
        assert obs.total_payable_fare is None

    def test_cancelled_with_price_rejected(self):
        with pytest.raises(ValidationError, match="must be null"):
            self._make(
                availability_status=AvailabilityStatus.CANCELLED,
                total_payable_fare=Decimal("500"),
            )

    def test_available_with_zero_price_rejected(self):
        """AVAILABLE observations must have a positive payable fare."""
        with pytest.raises(ValidationError, match="must be positive"):
            self._make(
                availability_status=AvailabilityStatus.AVAILABLE,
                total_payable_fare=Decimal("0"),
            )

    def test_available_with_null_price_ok(self):
        """Price may be missing even for AVAILABLE (parser couldn't extract it)."""
        obs = self._make(
            availability_status=AvailabilityStatus.AVAILABLE,
            total_payable_fare=None,
        )
        assert obs.total_payable_fare is None

    def test_bad_airport_code_rejected(self):
        with pytest.raises(ValidationError, match="3 uppercase letters"):
            self._make(origin_airport="xx")

    def test_bad_currency_rejected(self):
        with pytest.raises(ValidationError, match="ISO 4217"):
            self._make(currency="X")

    def test_uuid_auto_generated(self):
        obs1 = self._make()
        obs2 = self._make()
        assert obs1.observation_id != obs2.observation_id

    def test_quality_score_out_of_range(self):
        with pytest.raises(ValidationError):
            self._make(quality_score=Decimal("101"))


# ===================================================================
# Schema package re-exports
# ===================================================================


class TestSchemaPackageReexports:
    def test_import_from_schemas(self):
        from app.schemas import Airport as A
        assert A is Airport
