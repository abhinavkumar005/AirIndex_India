# Project Status

**Current phase:** Phase 6 — FastAPI Services and REST API  
**Status:** COMPLETE; Phase 7+ awaiting approval  
**Last updated:** 2026-09-12

## Completed

- Established modular monorepo directory structure.
- Created project-control and long-term memory documents.
- Defined initial architecture, compliance boundaries, data model plan, API contract plan, testing strategy, security baseline, and deployment plan.
- Added environment and configurable prototype settings examples.
- Initialized Git repository metadata locally.
- **Phase 1: Typed domain models and validated configuration loaders.**
  - 11 domain enums, 13 Pydantic v2 models, YAML loaders, prototype reference data.
  - 88 unit tests.
- **Phase 2: PostgreSQL schema and Alembic migrations.**
  - 11 SQLAlchemy 2.0 ORM tables with CHECK constraints, composite indexes, naming conventions.
  - Alembic migration framework with initial migration.
  - 18 ORM tests.
- **Phase 3: Realistic, deterministic mock airfare provider.**
  - Route-specific base fare ranges calibrated to Indian domestic levels.
  - Airline-specific fare multipliers (budget vs full-service).
  - Advance-purchase pricing curves (T+1 through T+45).
  - Day-of-week variation, fare component decomposition, configurable unavailability.
  - Deterministic with seeded randomness.
  - 16 tests.
- **Phase 4: Data pipeline (validation, cleaning, dedup, outliers, quality).**
  - Validator: temporal consistency, price-availability, fare range sanity, component sum checks.
  - Cleaner: field normalization (currency, codes).
  - Deduplicator: hash-key based with latest-observation retention.
  - Outlier detector: IQR-based flag-only (no deletion, per STATISTICAL_METHODOLOGY.md).
  - Quality scorer: 5-factor weighted composite (completeness, temporal, price, components, source).
  - Full pipeline orchestrator chaining all stages.
  - 18 tests.
- **Phase 5: Representative fares and configurable index engine.**
  - Configurable representative fare statistic (median/mean/trimmed_mean).
  - Price relative calculation with explicit base-period support.
  - Weighted aggregation into composite daily APIx values.
  - Weekly and monthly index aggregation from daily values.
  - Coverage tracking and eligibility handling.
  - Full provenance metadata (config version, calculation version, coverage).
  - 12 tests + 1 end-to-end integration test.
  - **160 total tests passing.**
- **Phase 6: FastAPI services and `/api/v1` REST API.**
  - Application factory with exception handlers, structured error bodies, health check, Swagger/ReDoc.
  - All 11 planned endpoints across 6 routers (index, routes, fares, sources, quality, validation).
  - Service layer (index, fare, route, quality) bridging pipeline + engine to the API.
  - Typed response schemas with `ApiEnvelope[T]`, pagination metadata, client-safe errors.
  - `Settings` via pydantic-settings reading `.env` (CORS origins, log level, feature flags) — closes a Phase 1 gap.
  - CORS restricted to configured origins (fail closed); exception handlers log with request IDs.
  - First-observation base-period fallback wired into the index service (previously every index value was trivially 100).
  - Mock generator flight counts made call-order independent (previously shared RNG state made API responses non-reproducible).
  - Pipeline now sets `quality_status` (VALID/FLAGGED) per DATA_DICTIONARY (previously stuck at PENDING).
  - 26 API tests including regression tests for the above fixes.
  - **187 total tests.**

## Current Work

- Phases 3–6 documented; awaiting Phase 7 approval.

## Pending

- Phase 7: React government/statistical dashboard.
- Phase 8: Source adapter framework and mock connector integration.
- Phase 9–15: Workers, external sources, backtesting, DGCA validation, deployment, demo.
- Index values are computed on-the-fly from the mock provider per request (see ADR-007); persistent storage of observations and index values in PostgreSQL arrives with Phase 8/9 wiring.

## Blockers / Required Inputs

- Official PSD/MoSPI methodology, base period, route basket, and weights are unavailable.
- DGCA reference dataset and usage terms have not been supplied.
- Authorization/compliance status for every airline and OTA source is unverified.
- Deployment target and administrative authentication approach require later owner decisions.

## Component Status

| Area | Status | Notes |
|---|---|---|
| Architecture | DOCUMENTED | Modular monorepo baseline; ADRs recorded |
| Domain models | IMPLEMENTED | Pydantic v2 models with validation; 88 tests |
| Config loaders | IMPLEMENTED | Validated YAML loaders for all 6 config files |
| Database | IMPLEMENTED | 11 ORM tables, Alembic migration, 18 ORM tests |
| Mock generator | IMPLEMENTED | Deterministic fare generation; 16 tests |
| Data pipeline | IMPLEMENTED | Validation, cleaning, dedup, outliers, quality; 18 tests |
| Index engine | IMPLEMENTED | Daily/weekly/monthly with provenance; 12 tests |
| API | IMPLEMENTED | 11 endpoints, service layer, envelope, Swagger; 27 tests |
| Frontend | SKELETON | Directories only; no React app yet |
| Collectors | SKELETON | Compliance-first adapter structure only |
| Testing | ACTIVE | 187 unit tests; 1 e2e integration test |
| Deployment | PLANNED | Compose topology documented; no runtime images yet |

## Known Bugs

None; tests are green.

## Next Recommended Task

With owner approval, implement Phase 7: React government/statistical dashboard (APIx overview, route explorer, lead-time elasticity, data quality, backtest validation views).
