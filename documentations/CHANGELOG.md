# Changelog

## Phase 6 — FastAPI Services and REST API (2026-09-12)

### Added

- `backend/app/core/config.py` — `Settings` (pydantic-settings) reading `.env`: environment, log level, service URLs, CORS origins, admin-auth and real-source-collection flags. Closes a Phase 1 plan gap.
- `backend/app/main.py` — FastAPI application factory: CORS from settings, logging-configured exception handlers with request IDs and client-safe error bodies, `/health`, Swagger/ReDoc.
- `backend/app/api/__init__.py`, `backend/app/api/v1/__init__.py` — API packages.
- `backend/app/api/v1/index.py` — `/api/v1/index/{current,daily,weekly,monthly,history}`.
- `backend/app/api/v1/routes.py` — `/api/v1/routes`, `/api/v1/routes/{route}/trend`.
- `backend/app/api/v1/fares.py` — `/api/v1/fares` (filters + pagination).
- `backend/app/api/v1/sources.py` — `/api/v1/sources/status` (compliance-aware).
- `backend/app/api/v1/quality.py` — `/api/v1/data-quality`.
- `backend/app/api/v1/validation.py` — `/api/v1/validation` (prototype backtest summary).
- `backend/app/schemas/responses.py` — `ApiEnvelope[T]`, pagination, error bodies, typed per-endpoint response models.
- `backend/app/services/{index,fare,route,quality}_service.py` — service layer bridging pipeline/engine/config to the API.
- `tests/unit/test_api.py` — 26 tests: all endpoints, envelope/meta, pagination, OpenAPI, plus regressions for idempotency, base-period fallback, and quality-status assignment.

### Changed

- `backend/app/services/index_service.py` — wired the first-observation base-period fallback: series anchor day = 100, subsequent days computed against anchor representative fares; `/index/current` trends measured against a shared 30-day anchor. Previously every index value was trivially 100 and all trends were 0. `base_period` is now disclosed per result.
- `backend/app/services/mock_fare_generator.py` — `generate_day` flight counts derived from a deterministic per-(route, airline, date, window) sub-seed instead of the instance's stateful RNG, making repeated generation of the same day idempotent (long-lived API services previously returned different values per request).
- `backend/app/services/pipeline.py` — stage 5 now sets `quality_status` (`VALID`/`FLAGGED`) on observations per DATA_DICTIONARY; previously observations stayed `PENDING` forever. Threshold 70.0 (prototype assumption).
- `backend/app/services/quality_service.py` — uses domain `quality_status` instead of an ad-hoc score threshold.
- `pyproject.toml` — added `pydantic-settings`.

### Tests

- **187 total tests** (160 prior + 26 API + 1 generator regression).

## Phase 5 — Representative Fares and Index Engine (2026-09-11)

### Added

- `backend/app/index_engine/__init__.py` — Index engine package.
- `backend/app/index_engine/engine.py` — Configurable index calculation engine: representative fare (median/mean/trimmed_mean), price relatives, weighted aggregation, daily/weekly/monthly computation, coverage tracking, provenance metadata.
- `tests/unit/test_index_engine.py` — 12 tests: representative fare, daily/weekly/monthly index, eligibility, outlier exclusion, provenance, end-to-end integration.

## Phase 4 — Data Pipeline (2026-09-11)

### Added

- `backend/app/services/pipeline.py` — Full processing pipeline: Validator (temporal/price/range checks), Cleaner (field normalization), Deduplicator (hash-key based), OutlierDetector (IQR flag-only), QualityScorer (5-factor weighted), FarePipeline orchestrator.
- `tests/unit/test_pipeline.py` — 18 tests: validator, cleaner, deduplicator, outlier detection, quality scoring, pipeline orchestration, mock generator integration.

## Phase 3 — Mock Airfare Generator (2026-09-11)

### Added

- `backend/app/services/__init__.py` — Services package.
- `backend/app/services/mock_fare_generator.py` — Deterministic mock fare generator: route-specific base fares (calibrated to INR domestic), airline multipliers (budget/full-service), advance-purchase curves, day-of-week variation, fare component decomposition, configurable sold-out/cancelled probability.
- `tests/unit/test_mock_fare_generator.py` — 16 tests: determinism, structure, pricing curves, components, availability, batch generation.

### Tests

- **160 total tests passing** (88 Phase 1 + 18 Phase 2 + 16 Phase 3 + 18 Phase 4 + 12 Phase 5 + 8 cross-phase).

## Phase 2 — PostgreSQL Schema and Alembic Migrations (2026-09-11)

### Added

- `backend/app/core/database.py` — SQLAlchemy 2.0 DeclarativeBase with PostgreSQL naming conventions, engine/session factory, FastAPI-compatible dependency.
- `backend/app/models/reference.py` — ORM models: `City`, `Airport`, `Airline`, `Route`, `Source`, `SourceConnector`.
- `backend/app/models/methodology.py` — ORM model: `RouteWeight` with effective date versioning.
- `backend/app/models/evidence.py` — ORM model: `FareRaw` (append-only raw storage with JSON payload).
- `backend/app/models/observations.py` — ORM model: `FareObservationModel` with full fare decomposition, CHECK constraints, composite indexes.
- `backend/app/models/outputs.py` — ORM models: `IndexValue`, `IndexComponent` with cascade delete.
- `backend/app/models/__init__.py` — Package init with re-exports.
- `alembic.ini` — Alembic configuration.
- `database/migrations/env.py` — Alembic environment with model auto-detection.
- `database/migrations/script.py.mako` — Migration template.
- `database/migrations/versions/001_initial_schema.py` — Initial migration creating all 11 tables.
- `tests/unit/test_orm_models.py` — 18 ORM tests.

### Changed

- `pyproject.toml` — Added SQLAlchemy ≥2.0, psycopg[binary] ≥3.1, Alembic ≥1.13.

## Phase 1 — Domain Models and Validated Configuration Loaders (2026-09-10)

### Added

- `pyproject.toml` — project metadata, dependencies (Pydantic v2, PyYAML), dev tools (pytest, pytest-cov).
- `backend/app/core/enums.py` — 11 domain enums.
- `backend/app/schemas/domain.py` — 13 Pydantic v2 models with cross-field validation.
- `backend/app/core/config_loader.py` — Validated YAML loaders.
- `configs/airports.yml` — 12 prototype Indian airports.
- `configs/airlines.yml` — 8 prototype Indian domestic airlines.
- Test files: 88 unit tests.

## Phase 0 — Repository Initialization (2026-09-07)

### Added

- Initial modular monorepo directory structure, 19 project-control documents, skeleton configs.
