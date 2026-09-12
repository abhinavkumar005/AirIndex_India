"""
API response schemas for AirIndex India.

Provides:
  - Generic API envelope with consistent structure
  - Pagination metadata
  - Error response models
  - Typed response models for each endpoint group

Status: DEMO / PROTOTYPE / ASSUMPTION
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Envelope and pagination
# ---------------------------------------------------------------------------


class PaginationMeta(BaseModel):
    """Pagination metadata for list endpoints."""

    total: int = Field(..., description="Total number of records")
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, le=500, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")


class ApiMeta(BaseModel):
    """Standard metadata block in API responses."""

    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="ISO 8601 UTC timestamp of response generation",
    )
    version: str = Field(default="v1", description="API version")
    pagination: Optional[PaginationMeta] = None


class ApiEnvelope(BaseModel, Generic[T]):
    """Standard API response envelope.

    All successful responses use this structure for consistency.
    """

    data: T
    meta: ApiMeta = Field(default_factory=ApiMeta)


class ErrorDetail(BaseModel):
    """A single error detail."""

    field: Optional[str] = None
    message: str


class ErrorResponse(BaseModel):
    """Standard error response body."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    request_id: Optional[str] = None
    details: list[ErrorDetail] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Index responses
# ---------------------------------------------------------------------------


class RouteComponentResponse(BaseModel):
    """Per-route breakdown in an index result."""

    model_config = ConfigDict(from_attributes=True)

    route_code: str
    representative_fare: Optional[Decimal] = None
    base_fare: Optional[Decimal] = None
    price_relative: Optional[Decimal] = None
    weight: float
    weighted_contribution: Optional[Decimal] = None
    observation_count: int
    excluded_count: int
    is_eligible: bool = True
    ineligibility_reason: Optional[str] = None


class IndexValueResponse(BaseModel):
    """A single index value with provenance metadata."""

    model_config = ConfigDict(from_attributes=True)

    frequency: str
    period_start: date
    period_end: date
    index_value: Optional[Decimal] = None
    base_period: Optional[str] = None
    config_version: str
    calculation_version: str
    coverage_pct: Decimal
    route_count: int
    eligible_route_count: int
    observation_count: int
    route_components: list[RouteComponentResponse] = Field(default_factory=list)


class CurrentIndexResponse(BaseModel):
    """Latest composite APIx value with key statistics."""

    model_config = ConfigDict(from_attributes=True)

    index_value: Optional[Decimal] = None
    frequency: str = "daily"
    as_of: date
    coverage_pct: Decimal
    route_count: int
    eligible_route_count: int
    observation_count: int
    config_version: str
    calculation_version: str
    trend_7d: Optional[Decimal] = None
    trend_30d: Optional[Decimal] = None


# ---------------------------------------------------------------------------
# Route responses
# ---------------------------------------------------------------------------


class RouteResponse(BaseModel):
    """A route in the configured basket."""

    model_config = ConfigDict(from_attributes=True)

    code: str
    origin: str
    destination: str
    weight: float
    effective_from: date
    effective_to: Optional[date] = None


class RouteTrendPoint(BaseModel):
    """A single data point in a route trend series."""

    date: date
    representative_fare: Optional[Decimal] = None
    price_relative: Optional[Decimal] = None
    observation_count: int = 0


class RouteTrendResponse(BaseModel):
    """Route-level fare/index trend over time."""

    route_code: str
    origin: str
    destination: str
    trend: list[RouteTrendPoint] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Fare responses
# ---------------------------------------------------------------------------


class FareObservationResponse(BaseModel):
    """Policy-safe fare observation view (no raw payloads)."""

    model_config = ConfigDict(from_attributes=True)

    observation_id: str
    observed_at: datetime
    source_code: str
    source_type: str
    origin_airport: str
    destination_airport: str
    departure_date: date
    airline_code: Optional[str] = None
    airline_name: Optional[str] = None
    flight_number: Optional[str] = None
    fare_class: Optional[str] = None
    advance_purchase_days: int
    base_fare: Optional[Decimal] = None
    taxes: Optional[Decimal] = None
    airport_charges: Optional[Decimal] = None
    user_development_fee: Optional[Decimal] = None
    convenience_fee: Optional[Decimal] = None
    other_charges: Optional[Decimal] = None
    total_payable_fare: Optional[Decimal] = None
    currency: str = "INR"
    availability_status: str
    quality_status: str
    quality_score: Optional[Decimal] = None


# ---------------------------------------------------------------------------
# Source responses
# ---------------------------------------------------------------------------


class SourceStatusResponse(BaseModel):
    """Connector health and authorization status."""

    model_config = ConfigDict(from_attributes=True)

    code: str
    source_type: str
    enabled: bool
    compliance_status: str
    rate_limit_per_minute: Optional[int] = None
    last_collection_at: Optional[datetime] = None
    observations_24h: int = 0
    health: str = "unknown"


# ---------------------------------------------------------------------------
# Quality responses
# ---------------------------------------------------------------------------


class QualitySummaryResponse(BaseModel):
    """Data quality summary for a period."""

    period_start: date
    period_end: date
    total_observations: int = 0
    valid_count: int = 0
    flagged_count: int = 0
    invalid_count: int = 0
    outlier_count: int = 0
    duplicate_count: int = 0
    average_quality_score: Optional[Decimal] = None
    coverage_by_route: dict[str, int] = Field(default_factory=dict)
    coverage_by_source: dict[str, int] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Validation / backtest responses
# ---------------------------------------------------------------------------


class ValidationSummaryResponse(BaseModel):
    """Backtest/reference validation summary."""

    period_start: date
    period_end: date
    backtest_days: int = 0
    average_index_value: Optional[Decimal] = None
    min_index_value: Optional[Decimal] = None
    max_index_value: Optional[Decimal] = None
    average_coverage_pct: Optional[Decimal] = None
    route_count: int = 0
    total_observations: int = 0
    status: str = "prototype"
