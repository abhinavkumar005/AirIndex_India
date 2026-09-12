# API Specification

## Status

IMPLEMENTED (Phase 6). FastAPI publishes OpenAPI documentation at `/docs` (Swagger) and `/redoc`. All data served by the prototype is synthetic (mock provider); index methodology parameters are prototype assumptions.

## Conventions

- Base path: `/api/v1`
- JSON responses with ISO 8601 UTC timestamps and stable public identifiers
- Validated filters, bounded pagination (`per_page` ≤ 500), consistent metadata, meaningful status codes, and client-safe errors
- Large collections return pagination metadata; internal database structures are never exposed directly
- Administrative mutation endpoints, when introduced, require authentication, authorization, and audit logging
- `GET` only in this phase; no mutation endpoints exist

## Implemented Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness/health check (outside `/api/v1`) |
| GET | `/api/v1/index/current` | Latest composite APIx with 7-day/30-day trends and coverage metadata |
| GET | `/api/v1/index/daily` | Daily index series (`start_date`, `end_date`; defaults to last 7 days) |
| GET | `/api/v1/index/weekly` | Weekly index series (defaults to last 28 days) |
| GET | `/api/v1/index/monthly` | Monthly index series (defaults to last 90 days) |
| GET | `/api/v1/index/history` | Filtered multi-frequency history (`frequency=daily|weekly|monthly`) |
| GET | `/api/v1/routes` | Configured/effective route basket with weights and effective dates |
| GET | `/api/v1/routes/{route}/trend` | Route-level representative fare / price-relative trend (`route` = e.g. `DEL-BOM`) |
| GET | `/api/v1/fares` | Paginated, policy-safe observation view (`observation_date`, `route`, `airline`, `page`, `per_page`) |
| GET | `/api/v1/sources/status` | Connector health and authorized availability (compliance-aware) |
| GET | `/api/v1/data-quality` | Coverage and quality summaries (`start_date`, `end_date`) |
| GET | `/api/v1/validation` | Prototype backtest summary statistics |

## Response Shape

Successful responses use a consistent envelope (`backend/app/schemas/responses.py`):

```json
{
  "data": { "...": "endpoint-specific payload" },
  "meta": {
    "generated_at": "2026-09-12T08:34:47Z",
    "version": "v1",
    "pagination": { "total": 622, "page": 1, "per_page": 50, "total_pages": 13 }
  }
}
```

`pagination` is `null` for non-list endpoints. Errors carry a stable `code`, safe `message`, `request_id`, and optional `details` list. Unhandled exceptions are logged server-side with the request ID and return a generic 500 body (no stack traces, paths, or internals).

### Index payload notes

- `index_value` is `null` when no eligible cells exist for a period (never zero).
- `base_period` discloses the base used. With the official base period unresolved (`index.yml: base_period: null`), the prototype applies a **first-observation fallback**: the first day of each requested series anchors at ~100 (and `/index/current` anchors 30 days back), so index levels are comparable within a series but not across differently-ranged requests. This is a disclosed prototype assumption (ADR-004/ADR-007).
- `route_components` provides per-route representative fare, price relative, weight, contribution, and eligibility.

## Data Protection

Raw payloads, internal errors, credentials, session data, and restricted source details are not public API fields. `/api/v1/fares` exposes only the policy-safe observation view. Query limits (`per_page` ≤ 500) bound expensive endpoints; rate controls arrive with the adapter framework (Phase 8).

## Prototype Limitations

- Observations and index values are computed on-the-fly from the deterministic mock provider per request (ADR-007); they are not yet persisted to PostgreSQL.
- `/api/v1/validation` reports backtest-style summary statistics only; DGCA reference comparison arrives in Phase 12.
- `/api/v1/sources/status` reports configuration-derived health (`healthy` for enabled sources); live connector health checks arrive with the adapter framework (Phase 8).
