# Testing Strategy

## Current Status

PLANNED. There is no executable application to test in Phase 0; repository/document consistency will be checked during initialization.

## Test Layers

- Unit: lead-time dates, fare parsing, validation, normalization, duplicate detection, outlier methods, quality scoring, representative fares, weighting, and index calculations.
- Integration: PostgreSQL repositories/migrations, API/service behavior, raw-to-index pipeline, Celery jobs, and configuration loading.
- End-to-end: mock data ingestion through dashboard/API, including the critical current-index and route-explorer flow.
- Contract: public API schemas and source-adapter interface behavior.

## Quality Gates

Python formatting/linting, type checks, pytest, migration tests, frontend lint/type/unit tests, production build, and Playwright smoke tests will be added with their respective phases. Tests must be deterministic; mock generation will accept a seed.

## Evidence Rule

Record the exact checks executed and their outcome. Never label a feature tested or validated based only on code inspection.
