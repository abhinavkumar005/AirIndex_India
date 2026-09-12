"""
Methodology ORM models.

Tables that record versioned statistical parameters: route weights,
effective dates, and configuration versions.

Tables: route_weights
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RouteWeight(Base):
    """A versioned weight assignment for a route in the index basket.

    Weights have effective date ranges and config version identifiers
    so that index calculations can reproduce historical results.
    """

    __tablename__ = "route_weights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    route_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("routes.id"), nullable=False
    )
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    config_version: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    # Relationships
    route: Mapped["Route"] = relationship("Route", back_populates="weights")

    __table_args__ = (
        CheckConstraint("weight > 0", name="weight_positive"),
        CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="effective_date_order",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<RouteWeight(route_id={self.route_id}, weight={self.weight}, "
            f"from={self.effective_from}, version={self.config_version!r})>"
        )


# Resolve forward reference
from app.models.reference import Route  # noqa: E402, F401
