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

Phase 1 is complete. The typed domain layer (enums, Pydantic v2 models, and validated YAML configuration loaders) is implemented under `backend/app/core/` and `backend/app/schemas/`. No runtime services, database schema, or API endpoints exist yet. 88 unit tests are passing.
