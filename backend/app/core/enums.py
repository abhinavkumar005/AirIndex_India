"""
Domain enumerations for AirIndex India.

These enums define the fixed vocabulary used across configuration files,
the data dictionary, and statistical methodology. Values are strings so
they serialize naturally to/from YAML, JSON, and database columns.

Status: DEMO / PROTOTYPE / ASSUMPTION — not official MoSPI/PSD/DGCA taxonomy.
"""

from enum import Enum


class SourceType(str, Enum):
    """Type of fare data source."""

    AIRLINE = "AIRLINE"
    OTA = "OTA"
    FEED = "FEED"
    MOCK = "MOCK"


class ComplianceStatus(str, Enum):
    """Authorization / compliance state of a data source."""

    APPROVED_FOR_SYNTHETIC_DEVELOPMENT = "APPROVED_FOR_SYNTHETIC_DEVELOPMENT"
    APPROVED = "APPROVED"
    UNKNOWN = "UNKNOWN"
    DENIED = "DENIED"
    REQUIRES_INDIVIDUAL_SOURCE_RECORDS = "REQUIRES_INDIVIDUAL_SOURCE_RECORDS"


class AvailabilityStatus(str, Enum):
    """Whether a fare observation represents a bookable flight."""

    AVAILABLE = "AVAILABLE"
    SOLD_OUT = "SOLD_OUT"
    CANCELLED = "CANCELLED"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    UNKNOWN = "UNKNOWN"


class CancellationStatus(str, Enum):
    """Flight operational status at observation time."""

    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"
    UNKNOWN = "UNKNOWN"


class QualityStatus(str, Enum):
    """Quality-pipeline processing outcome for an observation."""

    PENDING = "PENDING"
    VALID = "VALID"
    FLAGGED = "FLAGGED"
    INVALID = "INVALID"


class FareClass(str, Enum):
    """Normalized cabin / fare class."""

    ECONOMY = "ECONOMY"
    PREMIUM_ECONOMY = "PREMIUM_ECONOMY"
    BUSINESS = "BUSINESS"
    FIRST = "FIRST"
    UNKNOWN = "UNKNOWN"


class IndexFrequency(str, Enum):
    """Time granularity for published index values."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class OutlierPolicy(str, Enum):
    """How outliers are treated during representative-fare calculation."""

    FLAG_ONLY = "flag_only"
    EXCLUDE = "exclude"
    CONFIGURABLE = "configurable"


class MissingCellPolicy(str, Enum):
    """Treatment when an observation cell has insufficient data."""

    UNRESOLVED_REQUIRES_APPROVAL = "unresolved_requires_approval"
    CARRY_FORWARD = "carry_forward"
    EXCLUDE = "exclude"
    REDISTRIBUTE = "redistribute"


class WeightRedistributionPolicy(str, Enum):
    """How route weights are adjusted when cells are missing."""

    UNRESOLVED_REQUIRES_APPROVAL = "unresolved_requires_approval"
    PROPORTIONAL = "proportional"
    EQUAL = "equal"
    NONE = "none"


class ConfigStatus(str, Enum):
    """Lifecycle status of a configuration version."""

    DEMO_PROTOTYPE_ASSUMPTION = "DEMO_PROTOTYPE_ASSUMPTION"
    APPROVED = "APPROVED"
    DEPRECATED = "DEPRECATED"
