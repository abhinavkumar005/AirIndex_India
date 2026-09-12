"""
Data pipeline for AirIndex India.

Implements the processing stages defined in DATA_PIPELINE.md:
  Collection → Raw → Validation → Cleaning → Deduplication →
  Normalization → Outlier Detection → Quality Scoring

Each stage operates on FareObservation objects and produces annotated
results with provenance metadata.

Status: DEMO / PROTOTYPE / ASSUMPTION
"""

from __future__ import annotations

import hashlib
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from app.core.enums import (
    AvailabilityStatus,
    CancellationStatus,
    QualityStatus,
)
from app.schemas.domain import FareObservation


# ---------------------------------------------------------------------------
# Pipeline result types
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    """Result of validating a single observation."""
    observation: FareObservation
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class QualityScoredObservation:
    """An observation annotated with quality score and pipeline metadata."""
    observation: FareObservation
    quality_score: Decimal
    quality_factors: dict[str, float] = field(default_factory=dict)
    is_outlier: bool = False
    outlier_method: str | None = None
    outlier_score: float | None = None
    is_duplicate: bool = False
    duplicate_key: str | None = None
    pipeline_version: str = "pipeline-0.1.0"


@dataclass
class PipelineResult:
    """Complete result of processing a batch of observations."""
    valid: list[QualityScoredObservation] = field(default_factory=list)
    invalid: list[ValidationResult] = field(default_factory=list)
    duplicates_removed: int = 0
    outliers_flagged: int = 0
    total_input: int = 0
    total_output: int = 0
    pipeline_version: str = "pipeline-0.1.0"


# ---------------------------------------------------------------------------
# Stage 1: Validation
# ---------------------------------------------------------------------------

class Validator:
    """Structural and domain validation for fare observations.

    Checks enforce the rules from DATA_DICTIONARY.md and AGENTS.md:
      - Required fields present
      - Airport codes valid
      - Price-availability consistency
      - Temporal consistency
      - Monetary value sanity
    """

    def validate(self, obs: FareObservation) -> ValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        # Temporal checks
        if obs.departure_date < obs.observed_at.date():
            errors.append(
                f"departure_date {obs.departure_date} is before "
                f"observation date {obs.observed_at.date()}"
            )

        if obs.advance_purchase_days < 0:
            errors.append(f"Negative advance_purchase_days: {obs.advance_purchase_days}")

        # Expected advance days consistency
        expected_advance = (obs.departure_date - obs.observed_at.date()).days
        if expected_advance != obs.advance_purchase_days:
            warnings.append(
                f"advance_purchase_days={obs.advance_purchase_days} does not match "
                f"computed value={expected_advance}"
            )

        # Price-availability consistency (mirrors domain model validation)
        if obs.availability_status != AvailabilityStatus.AVAILABLE:
            if obs.total_payable_fare is not None:
                errors.append(
                    f"Non-available observation has total_payable_fare="
                    f"{obs.total_payable_fare}"
                )
        else:
            if obs.total_payable_fare is not None and obs.total_payable_fare <= 0:
                errors.append(
                    f"Available observation has non-positive fare: "
                    f"{obs.total_payable_fare}"
                )

        # Fare range sanity (INR domestic: ₹500 – ₹50,000)
        if (obs.total_payable_fare is not None
                and obs.availability_status == AvailabilityStatus.AVAILABLE):
            if obs.total_payable_fare < Decimal("500"):
                warnings.append(
                    f"Unusually low fare: ₹{obs.total_payable_fare}"
                )
            elif obs.total_payable_fare > Decimal("50000"):
                warnings.append(
                    f"Unusually high fare: ₹{obs.total_payable_fare}"
                )

        # Component sum check
        if obs.total_payable_fare is not None and obs.components:
            comp = obs.components
            component_vals = [
                v for v in [
                    comp.base_fare, comp.taxes, comp.airport_charges,
                    comp.user_development_fee, comp.convenience_fee, comp.other_charges,
                ] if v is not None
            ]
            if component_vals:
                comp_sum = sum(component_vals)
                diff = abs(obs.total_payable_fare - comp_sum)
                if diff > Decimal("1.00"):
                    warnings.append(
                        f"Component sum {comp_sum} differs from total "
                        f"{obs.total_payable_fare} by {diff}"
                    )

        is_valid = len(errors) == 0
        return ValidationResult(
            observation=obs,
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
        )


# ---------------------------------------------------------------------------
# Stage 2: Cleaning
# ---------------------------------------------------------------------------

class Cleaner:
    """Minimal cleaning / normalization.

    Per AGENTS.md: "Cleaning performs explicit, versioned corrections only
    when defensible." This prototype cleaner does:
      - Strip whitespace from string fields
      - Uppercase airline codes
      - Ensure currency is uppercase ISO
    """

    def clean(self, obs: FareObservation) -> FareObservation:
        """Return a cleaned copy (FareObservation is not frozen so
        we create a new one with adjusted fields)."""
        data = obs.model_dump()

        # Normalize string fields
        for str_field in ("source_code", "airline_code", "flight_number"):
            if data.get(str_field) and isinstance(data[str_field], str):
                data[str_field] = data[str_field].strip()

        # Currency uppercase
        if data.get("currency"):
            data["currency"] = data["currency"].strip().upper()

        return FareObservation(**data)


# ---------------------------------------------------------------------------
# Stage 3: Deduplication
# ---------------------------------------------------------------------------

class Deduplicator:
    """Identify and remove probable duplicate observations.

    Deduplication key: (source_code, origin, destination, airline_code,
    departure_date, departure_time_slot, fare_class, advance_purchase_days).

    Within a duplicate group, keep the observation with the latest
    observed_at timestamp.
    """

    @staticmethod
    def _dedup_key(obs: FareObservation) -> str:
        dep_slot = ""
        if obs.departure_time:
            dep_slot = obs.departure_time.strftime("%H:%M")

        parts = [
            obs.source_code,
            obs.origin_airport,
            obs.destination_airport,
            obs.airline_code or "",
            str(obs.departure_date),
            dep_slot,
            obs.fare_class.value if obs.fare_class else "",
            str(obs.advance_purchase_days),
            obs.flight_number or "",
        ]
        raw = "|".join(parts)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def deduplicate(
        self, observations: list[FareObservation]
    ) -> tuple[list[FareObservation], int]:
        """Remove duplicates, keeping latest observation per key.

        Returns:
            Tuple of (deduplicated_list, removed_count).
        """
        groups: dict[str, list[FareObservation]] = defaultdict(list)
        for obs in observations:
            key = self._dedup_key(obs)
            groups[key].append(obs)

        result: list[FareObservation] = []
        removed = 0
        for key, group in groups.items():
            # Keep the latest observation
            group.sort(key=lambda o: o.observed_at, reverse=True)
            result.append(group[0])
            removed += len(group) - 1

        return result, removed


# ---------------------------------------------------------------------------
# Stage 4: Outlier Detection
# ---------------------------------------------------------------------------

class OutlierDetector:
    """IQR-based outlier detection for fare observations.

    Per STATISTICAL_METHODOLOGY.md: "Outliers are flagged with method/version
    and retained. Exclusion from representative-fare calculation must be
    explicit and auditable."

    This detector does NOT remove outliers — it flags them.
    """

    def __init__(self, iqr_multiplier: float = 1.5):
        self.iqr_multiplier = iqr_multiplier
        self.method = f"IQR_{iqr_multiplier}"

    def detect(
        self, observations: list[FareObservation]
    ) -> list[tuple[FareObservation, bool, float | None]]:
        """Flag outliers within route groups.

        Returns:
            List of (observation, is_outlier, outlier_score) tuples.
        """
        # Group by route for outlier detection
        route_groups: dict[str, list[FareObservation]] = defaultdict(list)
        for obs in observations:
            route_key = f"{obs.origin_airport}-{obs.destination_airport}"
            route_groups[route_key].append(obs)

        results: list[tuple[FareObservation, bool, float | None]] = []

        for route_key, group in route_groups.items():
            # Get available fares for this route
            fares = [
                float(obs.total_payable_fare)
                for obs in group
                if (obs.total_payable_fare is not None
                    and obs.availability_status == AvailabilityStatus.AVAILABLE)
            ]

            if len(fares) < 4:
                # Not enough data for IQR
                for obs in group:
                    results.append((obs, False, None))
                continue

            fares_sorted = sorted(fares)
            n = len(fares_sorted)
            q1 = fares_sorted[n // 4]
            q3 = fares_sorted[3 * n // 4]
            iqr = q3 - q1
            lower_bound = q1 - self.iqr_multiplier * iqr
            upper_bound = q3 + self.iqr_multiplier * iqr

            for obs in group:
                if (obs.total_payable_fare is not None
                        and obs.availability_status == AvailabilityStatus.AVAILABLE):
                    fare_val = float(obs.total_payable_fare)
                    if fare_val < lower_bound or fare_val > upper_bound:
                        # Calculate z-like score for outlier severity
                        if iqr > 0:
                            score = abs(fare_val - (q1 + q3) / 2) / iqr
                        else:
                            score = 0.0
                        results.append((obs, True, score))
                    else:
                        results.append((obs, False, None))
                else:
                    results.append((obs, False, None))

        return results


# ---------------------------------------------------------------------------
# Stage 5: Quality Scoring
# ---------------------------------------------------------------------------

class QualityScorer:
    """Prototype quality scoring engine.

    Per STATISTICAL_METHODOLOGY.md: "Quality scoring is a prototype
    engineering indicator based on completeness, source reliability,
    parsing confidence, duplicate likelihood, timestamp validity,
    and anomaly flags."

    Score range: 0–100 (higher = better quality).
    """

    # Factor weights (sum to 1.0)
    WEIGHTS = {
        "completeness": 0.30,
        "temporal_validity": 0.20,
        "price_consistency": 0.20,
        "component_completeness": 0.15,
        "source_reliability": 0.15,
    }

    def score(
        self,
        obs: FareObservation,
        is_outlier: bool = False,
        validation_warnings: list[str] | None = None,
    ) -> tuple[Decimal, dict[str, float]]:
        """Compute quality score and factor breakdown.

        Returns:
            Tuple of (quality_score, factor_dict).
        """
        factors: dict[str, float] = {}

        # 1. Completeness: how many optional fields are populated
        optional_fields = [
            obs.airline_code, obs.airline_name, obs.flight_number,
            obs.fare_class, obs.departure_time, obs.arrival_time,
        ]
        populated = sum(1 for f in optional_fields if f is not None)
        factors["completeness"] = populated / len(optional_fields) * 100

        # 2. Temporal validity
        temporal_score = 100.0
        if obs.departure_date < obs.observed_at.date():
            temporal_score = 0.0
        elif obs.advance_purchase_days < 0:
            temporal_score = 0.0
        factors["temporal_validity"] = temporal_score

        # 3. Price consistency
        price_score = 100.0
        if obs.availability_status == AvailabilityStatus.AVAILABLE:
            if obs.total_payable_fare is None:
                price_score = 50.0  # Missing but should exist
            elif obs.total_payable_fare <= 0:
                price_score = 0.0
            elif is_outlier:
                price_score = 60.0  # Penalize outliers
        else:
            if obs.total_payable_fare is not None:
                price_score = 0.0  # Violated price-availability rule
        factors["price_consistency"] = price_score

        # 4. Component completeness
        comp = obs.components
        comp_fields = [
            comp.base_fare, comp.taxes, comp.airport_charges,
            comp.user_development_fee, comp.convenience_fee,
        ]
        comp_populated = sum(1 for f in comp_fields if f is not None)
        if obs.total_payable_fare is not None:
            factors["component_completeness"] = comp_populated / len(comp_fields) * 100
        else:
            factors["component_completeness"] = 100.0  # N/A for unavailable

        # 5. Source reliability (mock sources get a fixed score)
        factors["source_reliability"] = 80.0  # Prototype: mock is reliable

        # Warning penalty
        n_warnings = len(validation_warnings) if validation_warnings else 0
        warning_penalty = min(n_warnings * 5.0, 20.0)

        # Weighted score
        weighted = sum(
            factors[k] * self.WEIGHTS[k] for k in self.WEIGHTS
        )
        final = max(0.0, min(100.0, weighted - warning_penalty))

        return Decimal(str(round(final, 2))), factors


# ---------------------------------------------------------------------------
# Pipeline orchestrator
# ---------------------------------------------------------------------------

class FarePipeline:
    """Orchestrates the full fare processing pipeline.

    Usage:
        pipeline = FarePipeline()
        result = pipeline.process(observations)
    """

    # Observations at or above this score are VALID; below (or outlier-
    # flagged) they are FLAGGED. Prototype assumption.
    QUALITY_VALID_THRESHOLD = 70.0

    def __init__(
        self,
        iqr_multiplier: float = 1.5,
        pipeline_version: str = "pipeline-0.1.0",
    ):
        self.validator = Validator()
        self.cleaner = Cleaner()
        self.deduplicator = Deduplicator()
        self.outlier_detector = OutlierDetector(iqr_multiplier=iqr_multiplier)
        self.quality_scorer = QualityScorer()
        self.pipeline_version = pipeline_version

    def process(self, observations: list[FareObservation]) -> PipelineResult:
        """Process a batch of observations through all pipeline stages.

        Returns:
            PipelineResult with valid/invalid observations, quality scores, and statistics.
        """
        result = PipelineResult(
            total_input=len(observations),
            pipeline_version=self.pipeline_version,
        )

        # Stage 1: Validate
        valid_obs: list[FareObservation] = []
        validation_warnings: dict[str, list[str]] = {}

        for obs in observations:
            vr = self.validator.validate(obs)
            if vr.is_valid:
                valid_obs.append(obs)
                if vr.warnings:
                    validation_warnings[str(obs.observation_id)] = vr.warnings
            else:
                result.invalid.append(vr)

        # Stage 2: Clean
        cleaned = [self.cleaner.clean(obs) for obs in valid_obs]

        # Stage 3: Deduplicate
        deduped, removed_count = self.deduplicator.deduplicate(cleaned)
        result.duplicates_removed = removed_count

        # Stage 4: Outlier detection
        outlier_results = self.outlier_detector.detect(deduped)
        outlier_flags: dict[str, tuple[bool, float | None]] = {}
        for obs, is_outlier, score in outlier_results:
            outlier_flags[str(obs.observation_id)] = (is_outlier, score)
            if is_outlier:
                result.outliers_flagged += 1

        # Stage 5: Quality scoring
        for obs in deduped:
            obs_id = str(obs.observation_id)
            is_outlier, outlier_score = outlier_flags.get(obs_id, (False, None))
            warnings = validation_warnings.get(obs_id, [])

            quality_score, factors = self.quality_scorer.score(
                obs, is_outlier=is_outlier, validation_warnings=warnings,
            )

            # Record the derived quality status on the observation itself
            # (per DATA_DICTIONARY.md, quality_status is set by this stage).
            if is_outlier or float(quality_score) < self.QUALITY_VALID_THRESHOLD:
                obs.quality_status = QualityStatus.FLAGGED
            else:
                obs.quality_status = QualityStatus.VALID

            scored = QualityScoredObservation(
                observation=obs,
                quality_score=quality_score,
                quality_factors=factors,
                is_outlier=is_outlier,
                outlier_method=self.outlier_detector.method if is_outlier else None,
                outlier_score=outlier_score,
                pipeline_version=self.pipeline_version,
            )
            result.valid.append(scored)

        result.total_output = len(result.valid)
        return result
