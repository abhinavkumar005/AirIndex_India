"""
Pure Pydantic v2 domain models for AirIndex India.

These models are database-independent — no SQLAlchemy coupling.
They are used for:
  - Validating YAML configuration files
  - Representing reference data (airports, airlines)
  - Typing fare observations through the pipeline
  - Providing a shared vocabulary for the entire codebase

Status: DEMO / PROTOTYPE / ASSUMPTION — not official MoSPI/PSD/DGCA taxonomy.
"""

from __future__ import annotations

import math
import re
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

_IATA_AIRPORT_RE = re.compile(r"^[A-Z]{3}$")
_AIRLINE_CODE_RE = re.compile(r"^[A-Z0-9]{2,3}$")
_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")

# ---------------------------------------------------------------------------
# Reference data models
# ---------------------------------------------------------------------------


class Airport(BaseModel):
    """An Indian domestic airport used in the prototype route basket."""

    model_config = ConfigDict(frozen=True)

    iata_code: str = Field(
        ..., description="3-letter uppercase IATA airport code", examples=["DEL"]
    )
    name: str = Field(
        ..., description="Airport display name", examples=["Indira Gandhi International Airport"]
    )
    city_code: str = Field(
        ..., description="City code for grouping", examples=["DEL"]
    )
    city_name: str = Field(
        ..., description="City display name", examples=["Delhi"]
    )
    active: bool = Field(
        default=True, description="Whether airport is active in the current basket"
    )

    @field_validator("iata_code")
    @classmethod
    def validate_iata_code(cls, v: str) -> str:
        v = v.strip().upper()
        if not _IATA_AIRPORT_RE.match(v):
            raise ValueError(f"IATA airport code must be 3 uppercase letters, got '{v}'")
        return v

    @field_validator("city_code")
    @classmethod
    def validate_city_code(cls, v: str) -> str:
        v = v.strip().upper()
        if not _IATA_AIRPORT_RE.match(v):
            raise ValueError(f"City code must be 3 uppercase letters, got '{v}'")
        return v


class Airline(BaseModel):
    """An Indian domestic airline."""

    model_config = ConfigDict(frozen=True)

    code: str = Field(
        ..., description="2–3 char IATA/ICAO carrier code", examples=["6E"]
    )
    name: str = Field(
        ..., description="Airline display name", examples=["IndiGo"]
    )
    active: bool = Field(
        default=True, description="Whether airline is active for collection"
    )

    @field_validator("code")
    @classmethod
    def validate_airline_code(cls, v: str) -> str:
        v = v.strip().upper()
        if not _AIRLINE_CODE_RE.match(v):
            raise ValueError(
                f"Airline code must be 2–3 uppercase alphanumeric characters, got '{v}'"
            )
        return v


# ---------------------------------------------------------------------------
# Configuration wrapper models (match YAML structure)
# ---------------------------------------------------------------------------


class Route(BaseModel):
    """A single route in the index basket with an assigned weight."""

    model_config = ConfigDict(frozen=True)

    code: str = Field(..., description="Route identifier, e.g. DEL-BOM")
    origin: str = Field(..., description="Origin IATA airport code")
    destination: str = Field(..., description="Destination IATA airport code")
    weight: float = Field(..., gt=0, le=1, description="Basket weight ∈ (0, 1]")
    effective_from: date = Field(..., description="Date from which this route entry is effective")
    effective_to: Optional[date] = Field(
        default=None, description="Date until which this route entry is effective (inclusive)"
    )

    @field_validator("origin", "destination")
    @classmethod
    def validate_airport_code(cls, v: str) -> str:
        v = v.strip().upper()
        if not _IATA_AIRPORT_RE.match(v):
            raise ValueError(f"Airport code must be 3 uppercase letters, got '{v}'")
        return v

    @model_validator(mode="after")
    def origin_differs_from_destination(self) -> Route:
        if self.origin == self.destination:
            raise ValueError(
                f"Origin and destination must differ, both are '{self.origin}'"
            )
        return self

    @model_validator(mode="after")
    def effective_date_order(self) -> Route:
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError(
                f"effective_to ({self.effective_to}) must not precede "
                f"effective_from ({self.effective_from})"
            )
        return self


class Source(BaseModel):
    """Configuration for a single data source."""

    model_config = ConfigDict(frozen=True)

    code: str = Field(..., description="Unique source identifier")
    type: SourceType = Field(..., description="Source category")
    enabled: bool = Field(default=False, description="Whether collection is active")
    compliance_status: ComplianceStatus = Field(
        default=ComplianceStatus.UNKNOWN,
        description="Authorization / compliance state",
    )
    rate_limit_per_minute: Optional[int] = Field(
        default=None, ge=1, description="Max requests per minute when enabled"
    )


class RouteConfig(BaseModel):
    """Top-level validated routes configuration (matches routes.yml)."""

    version: str = Field(..., description="Configuration version identifier")
    status: ConfigStatus = Field(
        default=ConfigStatus.DEMO_PROTOTYPE_ASSUMPTION,
        description="Lifecycle status of this configuration",
    )
    description: Optional[str] = Field(
        default=None, description="Human-readable description"
    )
    routes: list[Route] = Field(..., min_length=1, description="Route basket entries")

    @model_validator(mode="after")
    def no_duplicate_route_codes(self) -> RouteConfig:
        codes = [r.code for r in self.routes]
        seen: set[str] = set()
        dupes: list[str] = []
        for c in codes:
            if c in seen:
                dupes.append(c)
            seen.add(c)
        if dupes:
            raise ValueError(f"Duplicate route codes: {dupes}")
        return self

    @model_validator(mode="after")
    def weights_sum_approximately_one(self) -> RouteConfig:
        total = math.fsum(r.weight for r in self.routes)
        if not math.isclose(total, 1.0, abs_tol=1e-6):
            raise ValueError(
                f"Route weights must sum to ≈1.0, got {total:.10f}"
            )
        return self


class SourceConfig(BaseModel):
    """Top-level validated sources configuration (matches sources.yml)."""

    version: str = Field(..., description="Configuration version identifier")
    default_enabled: bool = Field(
        default=False, description="Default enabled state for unlisted sources"
    )
    sources: list[Source] = Field(..., min_length=1, description="Configured sources")

    @model_validator(mode="after")
    def no_duplicate_source_codes(self) -> SourceConfig:
        codes = [s.code for s in self.sources]
        seen: set[str] = set()
        dupes: list[str] = []
        for c in codes:
            if c in seen:
                dupes.append(c)
            seen.add(c)
        if dupes:
            raise ValueError(f"Duplicate source codes: {dupes}")
        return self


class AdvanceWindowConfig(BaseModel):
    """Advance-purchase day windows (matches advance_windows.yml)."""

    version: str = Field(..., description="Configuration version identifier")
    status: ConfigStatus = Field(
        default=ConfigStatus.DEMO_PROTOTYPE_ASSUMPTION,
        description="Lifecycle status",
    )
    advance_purchase_days: list[int] = Field(
        ..., min_length=1, description="Sorted, unique positive lead-time days"
    )

    @field_validator("advance_purchase_days")
    @classmethod
    def validate_days(cls, v: list[int]) -> list[int]:
        if any(d < 1 for d in v):
            raise ValueError("All advance_purchase_days must be positive integers")
        if len(v) != len(set(v)):
            raise ValueError("advance_purchase_days must be unique")
        return sorted(v)


class IndexConfig(BaseModel):
    """Index calculation settings (matches index.yml)."""

    version: str = Field(..., description="Configuration version identifier")
    status: ConfigStatus = Field(
        default=ConfigStatus.DEMO_PROTOTYPE_ASSUMPTION,
        description="Lifecycle status",
    )
    currency: str = Field(
        default="INR", description="ISO 4217 currency code"
    )
    representative_fare_statistic: str = Field(
        default="median",
        description="Statistic used to compute representative fare (e.g. median, mean)",
    )
    base_period: Optional[str] = Field(
        default=None,
        description="Base period identifier; null until officially approved",
    )
    frequencies: list[IndexFrequency] = Field(
        ..., min_length=1, description="Index publication frequencies"
    )
    minimum_cell_observations: int = Field(
        default=1, ge=1,
        description="Minimum observations required per cell",
    )
    outlier_policy: OutlierPolicy = Field(
        default=OutlierPolicy.FLAG_ONLY,
        description="Outlier treatment approach",
    )
    missing_cell_policy: MissingCellPolicy = Field(
        default=MissingCellPolicy.UNRESOLVED_REQUIRES_APPROVAL,
        description="Treatment for cells with insufficient data",
    )
    weight_redistribution_policy: WeightRedistributionPolicy = Field(
        default=WeightRedistributionPolicy.UNRESOLVED_REQUIRES_APPROVAL,
        description="How route weights are adjusted for missing cells",
    )

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        v = v.strip().upper()
        if not _CURRENCY_RE.match(v):
            raise ValueError(f"Currency must be 3 uppercase letters (ISO 4217), got '{v}'")
        return v


# ---------------------------------------------------------------------------
# Reference-data config wrappers (for airports.yml / airlines.yml)
# ---------------------------------------------------------------------------


class AirportConfig(BaseModel):
    """Top-level wrapper for the airports reference file."""

    version: str
    status: ConfigStatus = ConfigStatus.DEMO_PROTOTYPE_ASSUMPTION
    airports: list[Airport] = Field(..., min_length=1)

    @model_validator(mode="after")
    def no_duplicate_iata_codes(self) -> AirportConfig:
        codes = [a.iata_code for a in self.airports]
        seen: set[str] = set()
        dupes: list[str] = []
        for c in codes:
            if c in seen:
                dupes.append(c)
            seen.add(c)
        if dupes:
            raise ValueError(f"Duplicate IATA codes: {dupes}")
        return self


class AirlineConfig(BaseModel):
    """Top-level wrapper for the airlines reference file."""

    version: str
    status: ConfigStatus = ConfigStatus.DEMO_PROTOTYPE_ASSUMPTION
    airlines: list[Airline] = Field(..., min_length=1)

    @model_validator(mode="after")
    def no_duplicate_airline_codes(self) -> AirlineConfig:
        codes = [a.code for a in self.airlines]
        seen: set[str] = set()
        dupes: list[str] = []
        for c in codes:
            if c in seen:
                dupes.append(c)
            seen.add(c)
        if dupes:
            raise ValueError(f"Duplicate airline codes: {dupes}")
        return self


# ---------------------------------------------------------------------------
# Aggregate project configuration
# ---------------------------------------------------------------------------


class ProjectConfig(BaseModel):
    """All validated configuration loaded from the configs/ directory."""

    routes: RouteConfig
    sources: SourceConfig
    advance_windows: AdvanceWindowConfig
    index: IndexConfig
    airports: AirportConfig
    airlines: AirlineConfig


# ---------------------------------------------------------------------------
# Fare observation models (used by pipeline, not by config loaders)
# ---------------------------------------------------------------------------


class FareComponent(BaseModel):
    """Decomposed fare components for a single observation.

    All monetary fields are non-negative when present.
    """

    base_fare: Optional[Decimal] = Field(default=None, ge=0)
    taxes: Optional[Decimal] = Field(default=None, ge=0)
    airport_charges: Optional[Decimal] = Field(default=None, ge=0)
    user_development_fee: Optional[Decimal] = Field(default=None, ge=0)
    convenience_fee: Optional[Decimal] = Field(default=None, ge=0)
    other_charges: Optional[Decimal] = Field(default=None, ge=0)


class FareObservation(BaseModel):
    """A single fare observation as defined in DATA_DICTIONARY.md.

    Key invariants:
      - total_payable_fare must be null when availability_status is not AVAILABLE
      - total_payable_fare must be positive when present
      - advance_purchase_days >= 0
      - origin != destination
    """

    observation_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    observed_at: datetime = Field(..., description="Collection timestamp (UTC)")
    source_code: str = Field(..., description="Configured source identifier")
    source_type: SourceType

    # Route
    origin_airport: str
    destination_airport: str
    origin_city: str
    destination_city: str

    # Schedule
    departure_date: date
    departure_time: Optional[datetime] = None
    arrival_time: Optional[datetime] = None

    # Carrier
    airline_code: Optional[str] = None
    airline_name: Optional[str] = None
    flight_number: Optional[str] = None
    fare_class: Optional[FareClass] = None

    # Pricing
    advance_purchase_days: int = Field(..., ge=0)
    components: FareComponent = Field(default_factory=FareComponent)
    total_payable_fare: Optional[Decimal] = Field(default=None)
    currency: str = Field(default="INR")

    # Status
    availability_status: AvailabilityStatus = Field(default=AvailabilityStatus.UNKNOWN)
    cancellation_status: CancellationStatus = Field(default=CancellationStatus.UNKNOWN)

    # Provenance
    raw_reference: Optional[dict[str, Any]] = Field(default=None)
    connector_version: str = Field(default="unknown")
    parser_version: str = Field(default="unknown")

    # Quality (set by pipeline, not by collectors)
    quality_status: QualityStatus = Field(default=QualityStatus.PENDING)
    quality_score: Optional[Decimal] = Field(default=None, ge=0, le=100)

    @field_validator("origin_airport", "destination_airport")
    @classmethod
    def validate_airport(cls, v: str) -> str:
        v = v.strip().upper()
        if not _IATA_AIRPORT_RE.match(v):
            raise ValueError(f"Airport code must be 3 uppercase letters, got '{v}'")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        v = v.strip().upper()
        if not _CURRENCY_RE.match(v):
            raise ValueError(f"Currency must be 3 uppercase letters (ISO 4217), got '{v}'")
        return v

    @model_validator(mode="after")
    def origin_differs_from_destination(self) -> FareObservation:
        if self.origin_airport == self.destination_airport:
            raise ValueError(
                f"Origin and destination must differ, both are '{self.origin_airport}'"
            )
        return self

    @model_validator(mode="after")
    def price_availability_consistency(self) -> FareObservation:
        """Enforce: non-available fares must not have a payable price.

        Per AGENTS.md / STATISTICAL_METHODOLOGY.md:
        'Never map sold-out, cancelled, or unavailable flights to zero price;
         use a null price and an explicit availability status.'
        """
        if self.availability_status != AvailabilityStatus.AVAILABLE:
            if self.total_payable_fare is not None:
                raise ValueError(
                    f"total_payable_fare must be null when availability_status "
                    f"is {self.availability_status.value}, got {self.total_payable_fare}"
                )
        else:
            if self.total_payable_fare is not None and self.total_payable_fare <= 0:
                raise ValueError(
                    f"total_payable_fare must be positive when AVAILABLE, "
                    f"got {self.total_payable_fare}"
                )
        return self
