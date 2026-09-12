"""
Fare observation ORM model.

Normalized, quality-scored fare observations derived from raw records.
This is the primary analytical table used by the index engine.

Tables: fare_observations
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import AvailabilityStatus, CancellationStatus, QualityStatus


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> uuid.UUID:
    return uuid.uuid4()


class FareObservationModel(Base):
    """Normalized fare observation for index calculation.

    This table holds cleaned, validated observations with decomposed fare
    components. Each row traces back to a fare_raw record and references
    lookup tables for airport, airline, and source identifiers.
    """

    __tablename__ = "fare_observations"

    # Identity
    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=_new_uuid
    )
    raw_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("fare_raw.id"), nullable=True,
        comment="FK to immutable raw record; null if ingested without raw layer",
    )

    # Observation metadata
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="Collection timestamp in UTC",
    )
    source_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sources.id"), nullable=False
    )

    # Route (FK to reference tables)
    origin_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("airports.id"), nullable=False
    )
    destination_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("airports.id"), nullable=False
    )

    # Carrier
    airline_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("airlines.id"), nullable=True
    )
    flight_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    fare_class: Mapped[str | None] = mapped_column(
        String(30), nullable=True, comment="FareClass enum value"
    )

    # Schedule
    departure_date: Mapped[date] = mapped_column(Date, nullable=False)
    departure_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    arrival_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    advance_purchase_days: Mapped[int] = mapped_column(Integer, nullable=False)

    # Fare components (all Numeric(12,2) for precision)
    base_fare: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    taxes: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    airport_charges: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    user_development_fee: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    convenience_fee: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    other_charges: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    total_payable_fare: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")

    # Status
    availability_status: Mapped[str] = mapped_column(
        String(20), nullable=False,
        default=AvailabilityStatus.UNKNOWN.value,
        comment="AvailabilityStatus enum value",
    )
    cancellation_status: Mapped[str] = mapped_column(
        String(20), nullable=False,
        default=CancellationStatus.UNKNOWN.value,
        comment="CancellationStatus enum value",
    )

    # Quality
    quality_status: Mapped[str] = mapped_column(
        String(20), nullable=False,
        default=QualityStatus.PENDING.value,
        comment="QualityStatus enum value",
    )
    quality_score: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )

    # Provenance
    connector_version: Mapped[str] = mapped_column(
        String(50), nullable=False, default="unknown"
    )
    parser_version: Mapped[str] = mapped_column(
        String(50), nullable=False, default="unknown"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    # Relationships
    source: Mapped["Source"] = relationship("Source")
    origin: Mapped["Airport"] = relationship("Airport", foreign_keys=[origin_id])
    destination: Mapped["Airport"] = relationship("Airport", foreign_keys=[destination_id])
    airline: Mapped["Airline | None"] = relationship("Airline")
    raw_record: Mapped["FareRaw | None"] = relationship(
        "FareRaw", back_populates="observations"
    )

    __table_args__ = (
        # Business rules as CHECK constraints
        CheckConstraint(
            "origin_id != destination_id",
            name="obs_origin_ne_destination",
        ),
        CheckConstraint(
            "advance_purchase_days >= 0",
            name="advance_days_non_negative",
        ),
        CheckConstraint(
            "base_fare IS NULL OR base_fare >= 0",
            name="base_fare_non_negative",
        ),
        CheckConstraint(
            "taxes IS NULL OR taxes >= 0",
            name="taxes_non_negative",
        ),
        CheckConstraint(
            "airport_charges IS NULL OR airport_charges >= 0",
            name="airport_charges_non_negative",
        ),
        CheckConstraint(
            "user_development_fee IS NULL OR user_development_fee >= 0",
            name="udf_non_negative",
        ),
        CheckConstraint(
            "convenience_fee IS NULL OR convenience_fee >= 0",
            name="convenience_fee_non_negative",
        ),
        CheckConstraint(
            "other_charges IS NULL OR other_charges >= 0",
            name="other_charges_non_negative",
        ),
        CheckConstraint(
            "length(currency) = 3",
            name="currency_iso_length",
        ),
        CheckConstraint(
            "quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 100)",
            name="quality_score_range",
        ),
        # Composite indexes for common query patterns
        Index("ix_obs_observed_source", "observed_at", "source_id"),
        Index("ix_obs_route_departure", "origin_id", "destination_id", "departure_date"),
        Index("ix_obs_departure_advance", "departure_date", "advance_purchase_days"),
        Index("ix_obs_quality_status", "quality_status"),
    )

    def __repr__(self) -> str:
        return (
            f"<FareObservation(id={self.id}, observed_at={self.observed_at}, "
            f"origin_id={self.origin_id}, destination_id={self.destination_id})>"
        )


# Resolve forward references
from app.models.reference import Airport, Airline, Source  # noqa: E402, F401
from app.models.evidence import FareRaw  # noqa: E402, F401
