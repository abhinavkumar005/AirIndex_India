"""
Index output ORM models.

Published index values and their per-route component breakdowns.

Tables: index_values, index_components
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> uuid.UUID:
    return uuid.uuid4()


class IndexValue(Base):
    """A published index value for a specific frequency and period.

    Each row captures the composite APIx value along with provenance
    metadata (config version, calculation version, coverage) so that
    any result can be reproduced.
    """

    __tablename__ = "index_values"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=_new_uuid
    )
    frequency: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="IndexFrequency enum value (daily/weekly/monthly)"
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    index_value: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), nullable=False,
        comment="Composite APIx value (base=100)",
    )
    base_period: Mapped[str | None] = mapped_column(
        String(50), nullable=True,
        comment="Base period identifier; null for prototype",
    )
    config_version: Mapped[str] = mapped_column(String(100), nullable=False)
    calculation_version: Mapped[str] = mapped_column(String(100), nullable=False)
    coverage_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True,
        comment="Percentage of route-cells with sufficient data",
    )
    route_count: Mapped[int] = mapped_column(Integer, nullable=False)
    observation_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    # Relationships
    components: Mapped[list[IndexComponent]] = relationship(
        "IndexComponent", back_populates="index_value", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint(
            "frequency", "period_start", "config_version",
            name="uq_index_freq_period_config",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<IndexValue(frequency={self.frequency!r}, "
            f"period={self.period_start}..{self.period_end}, "
            f"value={self.index_value})>"
        )


class IndexComponent(Base):
    """Per-route contribution to an index value.

    Records the representative fare, price relative, weight, and
    weighted contribution for each route in a given index calculation.
    """

    __tablename__ = "index_components"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=_new_uuid
    )
    index_value_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("index_values.id", ondelete="CASCADE"),
        nullable=False,
    )
    route_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("routes.id"), nullable=False
    )
    representative_fare: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True,
        comment="Computed representative fare for this route-cell",
    )
    base_fare_ref: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True,
        comment="Base-period representative fare for price-relative calculation",
    )
    price_relative: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 4), nullable=True,
        comment="current / base * 100",
    )
    weight: Mapped[float] = mapped_column(
        Float, nullable=False, comment="Route weight used in this calculation"
    )
    weighted_contribution: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 4), nullable=True,
        comment="price_relative * weight",
    )
    observation_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    excluded_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0,
        comment="Observations excluded due to quality/outlier rules",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    # Relationships
    index_value: Mapped[IndexValue] = relationship(
        "IndexValue", back_populates="components"
    )
    route: Mapped["Route"] = relationship("Route")

    def __repr__(self) -> str:
        return (
            f"<IndexComponent(index_value_id={self.index_value_id}, "
            f"route_id={self.route_id}, price_relative={self.price_relative})>"
        )


# Resolve forward references
from app.models.reference import Route  # noqa: E402, F401
