# Architecture

## System Goal

AirIndex India collects permitted airfare observations, preserves raw evidence, produces quality-controlled normalized records, constructs configurable statistical indices, and exposes audited results through an API and dashboard.

## Logical Flow

```text
Authorized or Mock Sources
  -> Compliance Gate and Rate Limits
  -> Source Adapters / Scheduler / Queue
  -> Collection Workers
  -> Immutable Raw Storage
  -> Validation / Cleaning / Deduplication / Normalization
  -> Outlier Flags / Quality Scoring
  -> Statistical Aggregation / Index Engine
  -> Analytics and Validation
  -> FastAPI
  -> React Dashboard and Government Consumers
```

## Repository Boundaries

- `collectors/`: adapter contracts, source-specific integrations, parsers, compliance checks, and scheduling concerns.
- `data_pipeline/`: deterministic transformations from raw to analysis-ready observations.
- `backend/app/index_engine/`: collector-independent statistical calculation.
- `backend/app/`: API, domain schemas, persistence models, repositories, services, and analytics.
- `database/`: migrations and seed/reference data.
- `frontend/`: government/statistical dashboard.
- `configs/`: versioned non-secret domain and prototype settings.

## Runtime Topology (Planned)

A modular monorepo deployed initially with Docker Compose: FastAPI API, collection/processing Celery workers, Celery Beat scheduler, PostgreSQL with optional TimescaleDB extension, Redis, React static frontend, and optional Nginx gateway. These are logical processes, not independent product microservices.

## Data Principles

Raw source payloads and collection metadata are append-only. Normalized observations reference raw records. Quality findings and exclusions are recorded, not erased. Index values reference calculation versions and component contributions so results are reproducible.

## Configuration

Environment variables configure runtime services and secrets. Version-controlled YAML files define non-secret prototype routes, sources, advance windows, and index settings. Effective dates will support evolving baskets and weights.

## Cross-Cutting Concerns

Structured events, health checks, rate limiting, safe error responses, authentication/authorization for administrative actions, audit logging, pagination, and retention-by-preservation apply across components.

## Current State

Phases 1–6 are complete. The typed domain layer (enums, Pydantic v2 models, validated YAML configuration loaders), the PostgreSQL ORM schema with Alembic migrations, the deterministic mock fare generator, the validation→cleaning→deduplication→outlier→quality pipeline, and the configurable index engine are implemented under `backend/app/`. The FastAPI application (`backend/app/main.py`) serves all 11 planned `/api/v1` endpoints with a service layer, typed response envelopes, settings-driven CORS, and Swagger/ReDoc docs. Per ADR-007, API responses are computed on-the-fly from the mock provider; persistence wiring, the adapter framework, workers, and the React dashboard are not yet implemented. 187 unit tests are passing.
