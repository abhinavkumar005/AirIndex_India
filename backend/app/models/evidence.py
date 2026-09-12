"""
Evidence-layer ORM models.

Append-only raw fare storage preserving original payloads and collection
metadata for auditability and parser reprocessing.

Tables: fare_raw
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> uuid.UUID:
    return uuid.uuid4()


class FareRaw(Base):
    """Immutable raw fare observation payload.

    Each row represents the raw data captured from a source during
    collection. These records are append-only — corrections create
    new derived records in fare_observations.
    """

    __tablename__ = "fare_raw"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=_new_uuid
    )
    source_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sources.id"), nullable=False
    )
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow,
        comment="UTC timestamp when data was collected",
    )
    raw_payload: Mapped[dict | None] = mapped_column(
        JSON, nullable=True,
        comment="Original source response or extracted fare data",
    )
    request_metadata: Mapped[dict | None] = mapped_column(
        JSON, nullable=True,
        comment="Collection request context (URL, params, headers hash)",
    )
    connector_version: Mapped[str] = mapped_column(
        String(50), nullable=False, default="unknown"
    )
    parser_version: Mapped[str] = mapped_column(
        String(50), nullable=False, default="unknown"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    # Relationships
    source: Mapped["Source"] = relationship("Source")
    observations: Mapped[list["FareObservationModel"]] = relationship(
        "FareObservationModel", back_populates="raw_record"
    )

    def __repr__(self) -> str:
        return (
            f"<FareRaw(id={self.id}, source_id={self.source_id}, "
            f"collected_at={self.collected_at})>"
        )


# Resolve forward references
from app.models.reference import Source  # noqa: E402, F401
from app.models.observations import FareObservationModel  # noqa: E402, F401
