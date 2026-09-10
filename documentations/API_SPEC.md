# API Specification

## Status

PLANNED. FastAPI will publish OpenAPI documentation. No endpoints are implemented yet.

## Conventions

- Base path: `/api/v1`
- JSON responses with ISO 8601 timestamps and stable public identifiers
- Validated filters, bounded pagination, consistent metadata, meaningful status codes, and client-safe errors
- Large collections return pagination metadata; internal database structures are never exposed directly
- Administrative mutation endpoints, when introduced, require authentication, authorization, and audit logging

## Planned Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/index/current` | Latest publishable composite APIx and coverage metadata |
| GET | `/api/v1/index/daily` | Daily index series |
| GET | `/api/v1/index/weekly` | Weekly index series |
| GET | `/api/v1/index/monthly` | Monthly index series |
| GET | `/api/v1/index/history` | Filtered multi-frequency history |
| GET | `/api/v1/routes` | Configured/effective route basket |
| GET | `/api/v1/routes/{route}/trend` | Route-level fare/index trend |
| GET | `/api/v1/fares` | Paginated, policy-safe observation view |
| GET | `/api/v1/sources/status` | Connector health and authorized availability |
| GET | `/api/v1/data-quality` | Coverage and quality summaries |
| GET | `/api/v1/validation` | Backtest/reference validation summaries |

## Response Shape

Successful responses should use a consistent envelope where useful: `data`, `meta`, and `generated_at`. Errors should include a stable code, safe message, request/correlation identifier, and optional field details. Exact schemas will be defined with Pydantic during Phase 6 and recorded here.

## Data Protection

Raw payloads, internal errors, credentials, session data, and restricted source details are not public API fields. Query limits and rate controls will protect expensive endpoints.
