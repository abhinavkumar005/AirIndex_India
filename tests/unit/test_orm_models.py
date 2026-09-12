"""
ORM model smoke tests.

Uses an in-memory SQLite database to verify:
  - All tables are created by Base.metadata.create_all()
  - Models can be instantiated and persisted
  - Foreign key relationships are traversable
  - Default values are applied correctly

NOTE: SQLite does not enforce CHECK constraints, so database-level
constraint validation is deferred to PostgreSQL integration tests.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker

from app.models import (
    Airline,
    Airport,
    Base,
    City,
    FareObservationModel,
    FareRaw,
    IndexComponent,
    IndexValue,
    Route,
    RouteWeight,
    Source,
    SourceConnector,
)


# ===================================================================
# Fixtures
# ===================================================================


@pytest.fixture()
def engine():
    """In-memory SQLite engine with all tables created."""
    eng = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture()
def session(engine):
    """SQLAlchemy session bound to the in-memory engine."""
    factory = sessionmaker(bind=engine)
    sess = factory()
    try:
        yield sess
    finally:
        sess.close()


@pytest.fixture()
def seed_reference(session: Session):
    """Insert minimal reference data and return a dict of created objects."""
    city_del = City(code="DEL", name="Delhi")
    city_bom = City(code="BOM", name="Mumbai")
    session.add_all([city_del, city_bom])
    session.flush()

    airport_del = Airport(
        iata_code="DEL", name="Indira Gandhi International", city_id=city_del.id
    )
    airport_bom = Airport(
        iata_code="BOM", name="Chhatrapati Shivaji Maharaj International", city_id=city_bom.id
    )
    session.add_all([airport_del, airport_bom])
    session.flush()

    airline = Airline(code="6E", name="IndiGo")
    session.add(airline)
    session.flush()

    route = Route(code="DEL-BOM", origin_id=airport_del.id, destination_id=airport_bom.id)
    session.add(route)
    session.flush()

    source = Source(
        code="MOCK_AIRLINE", source_type="MOCK", enabled=True,
        compliance_status="APPROVED_FOR_SYNTHETIC_DEVELOPMENT",
    )
    session.add(source)
    session.flush()

    session.commit()
    return {
        "city_del": city_del,
        "city_bom": city_bom,
        "airport_del": airport_del,
        "airport_bom": airport_bom,
        "airline": airline,
        "route": route,
        "source": source,
    }


# ===================================================================
# Schema creation
# ===================================================================


class TestSchemaCreation:
    def test_all_tables_exist(self, engine):
        inspector = inspect(engine)
        table_names = set(inspector.get_table_names())
        expected = {
            "cities", "airports", "airlines", "routes",
            "sources", "source_connectors",
            "route_weights",
            "fare_raw",
            "fare_observations",
            "index_values", "index_components",
        }
        assert expected.issubset(table_names), (
            f"Missing tables: {expected - table_names}"
        )

    def test_table_count(self, engine):
        inspector = inspect(engine)
        assert len(inspector.get_table_names()) == 11


# ===================================================================
# Reference models
# ===================================================================


class TestCityModel:
    def test_create_and_query(self, session: Session):
        city = City(code="JAI", name="Jaipur")
        session.add(city)
        session.commit()

        result = session.query(City).filter_by(code="JAI").one()
        assert result.name == "Jaipur"
        assert result.id is not None

    def test_default_created_at(self, session: Session):
        city = City(code="GOI", name="Goa")
        session.add(city)
        session.commit()
        assert city.created_at is not None


class TestAirportModel:
    def test_create_with_city_fk(self, session: Session, seed_reference):
        airport = session.query(Airport).filter_by(iata_code="DEL").one()
        assert airport.city.code == "DEL"
        assert airport.city.name == "Delhi"

    def test_city_airports_relationship(self, session: Session, seed_reference):
        city = session.query(City).filter_by(code="DEL").one()
        assert len(city.airports) == 1
        assert city.airports[0].iata_code == "DEL"


class TestAirlineModel:
    def test_create_and_query(self, session: Session, seed_reference):
        airline = session.query(Airline).filter_by(code="6E").one()
        assert airline.name == "IndiGo"
        assert airline.active is True


class TestRouteModel:
    def test_create_with_airports(self, session: Session, seed_reference):
        route = session.query(Route).filter_by(code="DEL-BOM").one()
        assert route.origin.iata_code == "DEL"
        assert route.destination.iata_code == "BOM"

    def test_airport_routes_relationship(self, session: Session, seed_reference):
        airport = session.query(Airport).filter_by(iata_code="DEL").one()
        assert len(airport.routes_as_origin) == 1
        assert airport.routes_as_origin[0].code == "DEL-BOM"


class TestSourceModel:
    def test_create_and_query(self, session: Session, seed_reference):
        source = session.query(Source).filter_by(code="MOCK_AIRLINE").one()
        assert source.source_type == "MOCK"
        assert source.enabled is True


class TestSourceConnectorModel:
    def test_create_with_source_fk(self, session: Session, seed_reference):
        ref = seed_reference
        connector = SourceConnector(
            source_id=ref["source"].id,
            connector_version="mock-0.1.0",
            parser_version="mock-0.1.0",
        )
        session.add(connector)
        session.commit()

        assert connector.source.code == "MOCK_AIRLINE"
        assert connector.active is True


# ===================================================================
# Methodology models
# ===================================================================


class TestRouteWeightModel:
    def test_create_and_query(self, session: Session, seed_reference):
        ref = seed_reference
        rw = RouteWeight(
            route_id=ref["route"].id,
            weight=0.1667,
            effective_from=date(2026, 9, 7),
            config_version="prototype-2026-09-07",
        )
        session.add(rw)
        session.commit()

        assert rw.route.code == "DEL-BOM"
        assert rw.weight == pytest.approx(0.1667)
        assert rw.effective_to is None


# ===================================================================
# Evidence models
# ===================================================================


class TestFareRawModel:
    def test_create_with_payload(self, session: Session, seed_reference):
        ref = seed_reference
        raw = FareRaw(
            source_id=ref["source"].id,
            raw_payload={"price": 4939, "airline": "6E"},
            request_metadata={"url": "https://mock.example.com"},
            connector_version="mock-0.1.0",
            parser_version="mock-0.1.0",
        )
        session.add(raw)
        session.commit()

        assert raw.id is not None
        assert isinstance(raw.id, uuid.UUID)
        assert raw.source.code == "MOCK_AIRLINE"
        assert raw.raw_payload["price"] == 4939


# ===================================================================
# Observation models
# ===================================================================


class TestFareObservationModel:
    def test_create_full_observation(self, session: Session, seed_reference):
        ref = seed_reference
        obs = FareObservationModel(
            observed_at=datetime(2026, 9, 7, 6, 30, tzinfo=timezone.utc),
            source_id=ref["source"].id,
            origin_id=ref["airport_del"].id,
            destination_id=ref["airport_bom"].id,
            airline_id=ref["airline"].id,
            flight_number="6E 123",
            fare_class="ECONOMY",
            departure_date=date(2026, 9, 14),
            advance_purchase_days=7,
            base_fare=Decimal("4200.00"),
            taxes=Decimal("310.00"),
            airport_charges=Decimal("150.00"),
            user_development_fee=Decimal("80.00"),
            convenience_fee=Decimal("199.00"),
            other_charges=Decimal("0.00"),
            total_payable_fare=Decimal("4939.00"),
            currency="INR",
            availability_status="AVAILABLE",
            cancellation_status="ACTIVE",
            quality_status="PENDING",
            connector_version="mock-0.1.0",
            parser_version="mock-0.1.0",
        )
        session.add(obs)
        session.commit()

        assert obs.id is not None
        assert isinstance(obs.id, uuid.UUID)
        assert obs.origin.iata_code == "DEL"
        assert obs.destination.iata_code == "BOM"
        assert obs.airline.code == "6E"
        assert obs.source.code == "MOCK_AIRLINE"
        assert obs.total_payable_fare == Decimal("4939.00")

    def test_observation_links_to_raw(self, session: Session, seed_reference):
        ref = seed_reference
        raw = FareRaw(
            source_id=ref["source"].id,
            connector_version="mock-0.1.0",
            parser_version="mock-0.1.0",
        )
        session.add(raw)
        session.flush()

        obs = FareObservationModel(
            raw_id=raw.id,
            observed_at=datetime(2026, 9, 7, 6, 30, tzinfo=timezone.utc),
            source_id=ref["source"].id,
            origin_id=ref["airport_del"].id,
            destination_id=ref["airport_bom"].id,
            departure_date=date(2026, 9, 14),
            advance_purchase_days=7,
            currency="INR",
            availability_status="AVAILABLE",
            cancellation_status="ACTIVE",
            quality_status="PENDING",
            connector_version="mock-0.1.0",
            parser_version="mock-0.1.0",
        )
        session.add(obs)
        session.commit()

        assert obs.raw_record is not None
        assert obs.raw_record.id == raw.id
        assert len(raw.observations) == 1

    def test_nullable_airline(self, session: Session, seed_reference):
        ref = seed_reference
        obs = FareObservationModel(
            observed_at=datetime(2026, 9, 7, 6, 30, tzinfo=timezone.utc),
            source_id=ref["source"].id,
            origin_id=ref["airport_del"].id,
            destination_id=ref["airport_bom"].id,
            departure_date=date(2026, 9, 14),
            advance_purchase_days=7,
            currency="INR",
            availability_status="UNKNOWN",
            cancellation_status="UNKNOWN",
            quality_status="PENDING",
            connector_version="mock-0.1.0",
            parser_version="mock-0.1.0",
        )
        session.add(obs)
        session.commit()

        assert obs.airline is None
        assert obs.airline_id is None


# ===================================================================
# Output models
# ===================================================================


class TestIndexValueModel:
    def test_create_with_components(self, session: Session, seed_reference):
        ref = seed_reference
        iv = IndexValue(
            frequency="daily",
            period_start=date(2026, 9, 7),
            period_end=date(2026, 9, 7),
            index_value=Decimal("100.0000"),
            config_version="prototype-2026-09-07",
            calculation_version="engine-0.1.0",
            route_count=1,
            observation_count=10,
        )
        session.add(iv)
        session.flush()

        comp = IndexComponent(
            index_value_id=iv.id,
            route_id=ref["route"].id,
            representative_fare=Decimal("4939.00"),
            base_fare_ref=Decimal("4939.00"),
            price_relative=Decimal("100.0000"),
            weight=1.0,
            weighted_contribution=Decimal("100.0000"),
            observation_count=10,
            excluded_count=0,
        )
        session.add(comp)
        session.commit()

        assert iv.id is not None
        assert len(iv.components) == 1
        assert iv.components[0].route.code == "DEL-BOM"
        assert iv.components[0].price_relative == Decimal("100.0000")


# ===================================================================
# Package re-exports
# ===================================================================


class TestModelPackageReexports:
    def test_all_models_importable(self):
        from app.models import (
            Base, City, Airport, Airline, Route, Source, SourceConnector,
            RouteWeight, FareRaw, FareObservationModel, IndexValue, IndexComponent,
        )
        # Verify Base.metadata has all tables
        table_names = set(Base.metadata.tables.keys())
        expected = {
            "cities", "airports", "airlines", "routes",
            "sources", "source_connectors",
            "route_weights", "fare_raw", "fare_observations",
            "index_values", "index_components",
        }
        assert expected == table_names
