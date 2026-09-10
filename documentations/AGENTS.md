# AirIndex India Agent Operating Guide

## Purpose

AirIndex India is a government-oriented prototype for auditable, high-frequency measurement of Indian domestic airfares and construction of a configurable airfare price index (APIx). It is not a booking or travel-recommendation product.

## Required Context

Before significant work, read `AGENTS.md`, `PROJECT_STATUS.md`, `ARCHITECTURE.md`, `KNOWN_ISSUES.md`, `ROADMAP.md`, and the documents relevant to the affected module.

## Architecture Rules

- Use a modular monorepo. Keep collection, raw storage, processing, index construction, APIs, and presentation separated.
- Preserve immutable raw observations. Derived records must retain provenance.
- Keep the index engine independent of collectors and runnable from stored database or file data.
- Implement source adapters behind a common interface; never build a single monolithic scraper.
- Prefer a modular monolith plus workers for the prototype. Do not introduce microservices without owner approval.
- All statistical parameters, routes, weights, base periods, schedules, and rate limits must be configurable.

## Technology Baseline

Python, FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL/optional TimescaleDB, Celery, Redis, React, TypeScript, Vite, Tailwind CSS, ECharts, Docker Compose, pytest, and frontend/Playwright tests. Replacing a core technology requires owner approval and an ADR.

## Engineering Standards

- Use type hints, focused functions, explicit naming, and docstrings on important public interfaces.
- Separate API, service, repository, schema, and persistence concerns where useful.
- Validate all external input and return client-safe structured errors.
- Use UTC timestamps internally and preserve source/local time context where needed.
- Add a migration for every schema change; never modify a production schema manually.
- Avoid hard-coded domain assumptions and silent exception handling.

## Statistical and Data Rules

- Never invent official MoSPI/PSD methodology, weights, base periods, or DGCA results.
- Mark all non-official parameters as `DEMO / PROTOTYPE / ASSUMPTION`.
- Never map sold-out, cancelled, or unavailable flights to zero price; use a null price and an explicit availability status.
- Flag suspected outliers rather than deleting them by default.
- Every published index value must be traceable to inputs, exclusions, weights, rules, and calculation version.

## Collection Compliance

- Verify authorization, robots.txt, terms, rate limits, and applicable policy before enabling a real source.
- Prefer authorized APIs, feeds, permitted public data, sandbox sources, or mock data.
- Never bypass CAPTCHA, authentication, access controls, bot protections, or source restrictions.
- A connector must fail closed when compliance status is unknown or disallowed.

## Security

- Never commit secrets, credentials, cookies, tokens, private certificates, or `.env` files.
- Use environment variables, least privilege, input validation, safe CORS defaults, structured logging, audit records, and protected admin operations.
- Do not expose stack traces, database internals, filesystem paths, or secrets through APIs.

## Testing

- Run relevant unit, integration, type, lint, and end-to-end checks before claiming completion.
- Tests must cover lead-time calculation, parsing, normalization, deduplication, outliers, quality scores, aggregation, weighting, index calculation, database behavior, APIs, and the critical dashboard flow as those features are implemented.
- Never report a test as passed unless it was executed.

## Documentation and Project Memory

For every meaningful change, assess and update at least `PROJECT_STATUS.md`, `CHANGELOG.md`, `ROADMAP.md`, `ARCHITECTURE.md`, `DATA_DICTIONARY.md`, `API_SPEC.md`, `DATABASE.md`, `STATISTICAL_METHODOLOGY.md`, and `KNOWN_ISSUES.md` where affected. Record significant decisions in `DECISIONS.md`.

## Forbidden Shortcuts

- No fabricated data presented as real validation.
- No destructive historical-data behavior or silent retention policy.
- No direct database-to-API exposure that bypasses domain validation.
- No scraping implementation that depends on evasion.
- No giant scraper, giant service, or premature microservice split.
- No claim of implementation, compliance, validation, or testing without evidence.

## User Control and Approval

Stop and request project-owner approval before changing core architecture, technology baseline, statistical methodology, route weights, database architecture, deployment architecture, major dependencies, compliance assumptions, or before destructive operations. Explain options, consequences, and the recommended choice. Use reversible steps and preserve user-created work.

## Change Workflow

Inspect context, plan the smallest correct change, implement it, verify it, synchronize documentation, and report exact changes, commands/tests run, limitations, and the recommended next task. Do not proceed automatically into a new major phase.
