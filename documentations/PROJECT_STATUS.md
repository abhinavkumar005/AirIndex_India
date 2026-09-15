# Project Status

**Current phase:** Phase 7 — React Government Dashboard  
**Status:** COMPLETE; Phase 8+ awaiting approval  
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
- **Phase 7: React government/statistical dashboard + database corrections.**
  - Vite + React 18 + TypeScript + Tailwind CSS + ECharts frontend (`frontend/`).
  - All 5 dashboard views: APIx Overview, Route Explorer (heatmap + drill-down), Lead-Time Elasticity, Data Quality Monitor, Backtest/Validation.
  - Typed API client mirroring backend response schemas; dev proxy to FastAPI (`:8000`).
  - New `GET /api/v1/index/lead-time` endpoint backed by `IndexEngine.compute_lead_time_cells()` — representative fares per route × advance-purchase window (closes the KNOWN_ISSUES lead-time gap without changing composite methodology).
  - Database corrections: `SessionLocal` typing + `init_db()`; removed unused imports in `evidence.py`.
  - Database seed layer (previously missing Phase 2 deliverable): `database/seed/airports.json`, `airlines.json`, idempotent `seed_loader.py`.
  - 2 new API tests (lead-time shape + determinism). **189 total tests.**

## Current Work

- Phase 7 complete and verified (build + live dev-server smoke test of all endpoints); awaiting Phase 8 approval.

## Pending

- Phase 8: Source adapter framework and mock connector integration.
- Phase 9–15: Workers, external sources, backtesting, DGCA validation, deployment, demo.
- Index values are computed on-the-fly from the mock provider per request (see ADR-007); persistent storage of observations and index values in PostgreSQL arrives with Phase 8/9 wiring.
- Live PostgreSQL on the development machine rejects the default `airindex/change-me` credentials — owner must supply actual credentials to run migrations/seed against it.

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
| API | IMPLEMENTED | 12 endpoints, service layer, envelope, Swagger; 28 tests |
| Frontend | IMPLEMENTED | Vite + React 18 + TS + Tailwind + ECharts; 5 dashboard views |
| Collectors | SKELETON | Compliance-first adapter structure only |
| Testing | ACTIVE | 189 unit tests; 1 e2e integration test |
| Deployment | PLANNED | Compose topology documented; no runtime images yet |

## Known Bugs

None; tests are green.

## Next Recommended Task

With owner approval, implement Phase 8: source adapter framework (registry, rate limiter, compliance gate) and mock connector integration into the pipeline, plus persistence wiring so observations and index values land in PostgreSQL.
