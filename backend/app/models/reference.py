"""
Reference data ORM models.

Small, slowly changing tables that provide the lookup vocabulary for
observations, routes, and index calculations.

Tables: cities, airports, airlines, routes, sources, source_connectors
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import ComplianceStatus, SourceType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Cities
# ---------------------------------------------------------------------------


class City(Base):
    """City reference for grouping airports."""

    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    # Relationships
    airports: Mapped[list[Airport]] = relationship("Airport", back_populates="city")

    def __repr__(self) -> str:
        return f"<City(code={self.code!r}, name={self.name!r})>"


# ---------------------------------------------------------------------------
# Airports
# ---------------------------------------------------------------------------


class Airport(Base):
    """Indian domestic airport with IATA code."""

    __tablename__ = "airports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    iata_code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    city_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cities.id"), nullable=False
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    # Relationships
    city: Mapped[City] = relationship("City", back_populates="airports")
    routes_as_origin: Mapped[list[Route]] = relationship(
        "Route", foreign_keys="Route.origin_id", back_populates="origin"
    )
    routes_as_destination: Mapped[list[Route]] = relationship(
        "Route", foreign_keys="Route.destination_id", back_populates="destination"
    )

    __table_args__ = (
        CheckConstraint(
            "length(iata_code) = 3",
            name="iata_code_length",
        ),
    )

    def __repr__(self) -> str:
        return f"<Airport(iata_code={self.iata_code!r}, name={self.name!r})>"


# ---------------------------------------------------------------------------
# Airlines
# ---------------------------------------------------------------------------


class Airline(Base):
    """Indian domestic airline carrier."""

    __tablename__ = "airlines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    __table_args__ = (
        CheckConstraint(
            "length(code) >= 2 AND length(code) <= 3",
            name="airline_code_length",
        ),
    )

    def __repr__(self) -> str:
        return f"<Airline(code={self.code!r}, name={self.name!r})>"


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


class Route(Base):
    """A directional route between two airports."""

    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    origin_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("airports.id"), nullable=False
    )
    destination_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("airports.id"), nullable=False
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    # Relationships
    origin: Mapped[Airport] = relationship(
        "Airport", foreign_keys=[origin_id], back_populates="routes_as_origin"
    )
    destination: Mapped[Airport] = relationship(
        "Airport", foreign_keys=[destination_id], back_populates="routes_as_destination"
    )
    weights: Mapped[list["RouteWeight"]] = relationship(
        "RouteWeight", back_populates="route"
    )

    __table_args__ = (
        CheckConstraint(
            "origin_id != destination_id",
            name="origin_ne_destination",
        ),
    )

    def __repr__(self) -> str:
        return f"<Route(code={self.code!r})>"


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------


class Source(Base):
    """A configured fare data source (airline site, OTA, feed, or mock)."""

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="SourceType enum value"
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    compliance_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=ComplianceStatus.UNKNOWN.value
    )
    rate_limit_per_minute: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    # Relationships
    connectors: Mapped[list[SourceConnector]] = relationship(
        "SourceConnector", back_populates="source"
    )

    def __repr__(self) -> str:
        return f"<Source(code={self.code!r}, type={self.source_type!r})>"


# ---------------------------------------------------------------------------
# Source Connectors
# ---------------------------------------------------------------------------


class SourceConnector(Base):
    """Versioned connector/parser for a data source."""

    __tablename__ = "source_connectors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sources.id"), nullable=False
    )
    connector_version: Mapped[str] = mapped_column(String(50), nullable=False)
    parser_version: Mapped[str] = mapped_column(String(50), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    # Relationships
    source: Mapped[Source] = relationship("Source", back_populates="connectors")

    __table_args__ = (
        UniqueConstraint(
            "source_id", "connector_version", "parser_version",
            name="uq_source_connector_version",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<SourceConnector(source_id={self.source_id}, "
            f"connector={self.connector_version!r}, parser={self.parser_version!r})>"
        )


# Forward reference import for type checkers
from app.models.methodology import RouteWeight  # noqa: E402, F401
