"""
Tests for domain enumerations.

Verifies that every enum class:
  - Is importable from both the module and the core package
  - Contains the expected members
  - Has the correct string values for serialization
"""

from __future__ import annotations

import pytest

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


class TestSourceType:
    def test_members(self):
        assert set(SourceType) == {
            SourceType.AIRLINE,
            SourceType.OTA,
            SourceType.FEED,
            SourceType.MOCK,
        }

    def test_string_values(self):
        assert SourceType.AIRLINE.value == "AIRLINE"
        assert SourceType.MOCK.value == "MOCK"

    def test_is_str(self):
        assert isinstance(SourceType.AIRLINE, str)


class TestComplianceStatus:
    def test_members(self):
        expected = {
            "APPROVED_FOR_SYNTHETIC_DEVELOPMENT",
            "APPROVED",
            "UNKNOWN",
            "DENIED",
            "REQUIRES_INDIVIDUAL_SOURCE_RECORDS",
        }
        assert {m.value for m in ComplianceStatus} == expected

    def test_synthetic_dev_value(self):
        assert ComplianceStatus("APPROVED_FOR_SYNTHETIC_DEVELOPMENT") == (
            ComplianceStatus.APPROVED_FOR_SYNTHETIC_DEVELOPMENT
        )


class TestAvailabilityStatus:
    def test_members(self):
        expected = {"AVAILABLE", "SOLD_OUT", "CANCELLED", "NOT_AVAILABLE", "UNKNOWN"}
        assert {m.value for m in AvailabilityStatus} == expected


class TestCancellationStatus:
    def test_members(self):
        expected = {"ACTIVE", "CANCELLED", "UNKNOWN"}
        assert {m.value for m in CancellationStatus} == expected


class TestQualityStatus:
    def test_members(self):
        expected = {"PENDING", "VALID", "FLAGGED", "INVALID"}
        assert {m.value for m in QualityStatus} == expected


class TestFareClass:
    def test_members(self):
        expected = {"ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST", "UNKNOWN"}
        assert {m.value for m in FareClass} == expected


class TestIndexFrequency:
    def test_lowercase_values(self):
        """IndexFrequency uses lowercase to match YAML convention."""
        assert IndexFrequency.DAILY.value == "daily"
        assert IndexFrequency.WEEKLY.value == "weekly"
        assert IndexFrequency.MONTHLY.value == "monthly"


class TestOutlierPolicy:
    def test_members(self):
        expected = {"flag_only", "exclude", "configurable"}
        assert {m.value for m in OutlierPolicy} == expected


class TestMissingCellPolicy:
    def test_members(self):
        expected = {
            "unresolved_requires_approval",
            "carry_forward",
            "exclude",
            "redistribute",
        }
        assert {m.value for m in MissingCellPolicy} == expected


class TestWeightRedistributionPolicy:
    def test_members(self):
        expected = {
            "unresolved_requires_approval",
            "proportional",
            "equal",
            "none",
        }
        assert {m.value for m in WeightRedistributionPolicy} == expected


class TestConfigStatus:
    def test_members(self):
        expected = {"DEMO_PROTOTYPE_ASSUMPTION", "APPROVED", "DEPRECATED"}
        assert {m.value for m in ConfigStatus} == expected


class TestCorePackageReexports:
    """Verify that enums are importable via the core package shortcut."""

    def test_import_from_core(self):
        from app.core import SourceType as ST
        assert ST is SourceType

    def test_all_enums_in_core(self):
        import app.core
        for name in [
            "AvailabilityStatus",
            "CancellationStatus",
            "ComplianceStatus",
            "ConfigStatus",
            "FareClass",
            "IndexFrequency",
            "MissingCellPolicy",
            "OutlierPolicy",
            "QualityStatus",
            "SourceType",
            "WeightRedistributionPolicy",
        ]:
            assert hasattr(app.core, name), f"{name} not re-exported from app.core"
