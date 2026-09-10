# AirIndex India

AirIndex India is a production-minded Smart India Hackathon 2026 prototype for measuring changes in Indian domestic airfares through permitted high-frequency observations, auditable data-quality processing, and a configurable Airfare Price Index (APIx). It is a statistical data platform—not a booking or travel-recommendation application.

## Why It Is Needed

Airfares change by route, airline, booking lead time, demand, season, availability, and fee composition. A digital collection and index platform can augment manual CPI-related price collection while improving frequency, coverage, reproducibility, and auditability.

## Planned Capabilities

- Compliance-first airline/OTA source adapters plus a first-class mock provider
- Immutable raw evidence and versioned validation/cleaning pipelines
- Explicit availability, fare-component, outlier, and quality treatment
- Configurable route basket, advance windows, weights, base period, and aggregation
- Traceable daily, weekly, monthly, route, lead-time, and national indices
- FastAPI government-facing APIs and React statistical dashboard
- 30-day backtesting and DGCA reference comparison when genuine data is supplied

## Architecture

```text
Permitted/Mock Sources -> Adapters -> Queue/Workers -> Raw Store
-> Quality Pipeline -> Index Engine -> Analytics -> FastAPI -> Dashboard/API Consumers
```

The initial deployment is a modular monorepo with logical API, worker, scheduler, database, Redis, and frontend processes. See `ARCHITECTURE.md`.

## Technology Baseline

Python, FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL, optional TimescaleDB, Celery, Redis, React, TypeScript, Vite, Tailwind CSS, ECharts, Docker Compose, pytest, and Playwright/frontend tests.

## Repository Structure

- `backend/` — planned API, domain, persistence, services, analytics, and index engine
- `collectors/` — adapter interfaces, mock and future approved source integrations
- `data_pipeline/` — validation, cleaning, normalization, deduplication, outliers, quality
- `database/` — migrations and seed/reference data
- `frontend/` — planned React dashboard
- `configs/` — non-secret, versioned prototype configuration
- `docs/` — focused architecture, methodology, data, API, development, deployment, testing, and decision records

## Current Status

Phase 0 is initialized. No application services are implemented or runnable yet. See `PROJECT_STATUS.md` and `ROADMAP.md`.

## Local Setup

1. Clone or open the repository.
2. Copy `.env.example` to a local `.env` only after services are implemented; never commit it.
3. Review `ENVIRONMENT.md` and the current `PROJECT_STATUS.md`.

Backend, frontend, worker, database, Docker, and test commands will be added during their implementation phases. The present `docker-compose.yml` is intentionally non-runnable documentation rather than a misleading partial deployment.

## Environment Variables

The initial contract includes `ENVIRONMENT`, `LOG_LEVEL`, `DATABASE_URL`, `REDIS_URL`, `API_BASE_URL`, and `CORS_ORIGINS`. See `.env.example` and `ENVIRONMENT.md`.

## Mock Data

Development will proceed using a deterministic mock provider so the raw-data, quality, index, API, and dashboard path does not depend on external website access. Mock outputs will be labeled synthetic.

## API Documentation

Planned endpoints are documented in `API_SPEC.md`. FastAPI Swagger/OpenAPI will be available only after Phase 6.

## Methodology

The prototype will calculate representative fares and price relatives using versioned configuration. No official methodology, weights, base period, or DGCA validation is claimed. See `STATISTICAL_METHODOLOGY.md`.

## Data-Source Compliance

Real connectors remain disabled until authorization and policy reviews are recorded. CAPTCHA, authentication, access-control, or rate-limit bypass is prohibited. See `SCRAPING_POLICY.md`.

## Limitations

This repository currently contains foundations and plans only. Official statistical inputs, DGCA data, source permissions, and deployment choices remain unresolved. See `KNOWN_ISSUES.md`.

## Roadmap

The next proposed phase is typed domain models and configuration validation, subject to project-owner approval. See `ROADMAP.md` and `DEVELOPMENT_PLAN.md`.
