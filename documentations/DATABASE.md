# Database Design

## Status

IMPLEMENTED (Phase 2). SQLAlchemy 2.0 ORM models and Alembic initial migration created. 11 tables across reference, evidence, methodology, observation, and output layers.

## Platform

PostgreSQL is the system of record. TimescaleDB is optional and will be enabled only when measured time-series benefits justify it. SQLAlchemy models and Alembic migrations control schema evolution.

## Implemented Tables (Phase 2)

### Reference (small, slowly changing)

| Table | Key Columns | Constraints |
|---|---|---|
| `cities` | `id`, `code` (UNIQUE), `name` | — |
| `airports` | `id`, `iata_code` (UNIQUE, CHECK len=3), `name`, `city_id` FK→cities | Active flag |
| `airlines` | `id`, `code` (UNIQUE, CHECK len 2–3), `name`, `active` | — |
| `routes` | `id`, `code` (UNIQUE), `origin_id` FK→airports, `destination_id` FK→airports | CHECK origin≠destination |
| `sources` | `id`, `code` (UNIQUE), `source_type`, `enabled`, `compliance_status` | Rate limit |
| `source_connectors` | `id`, `source_id` FK→sources, `connector_version`, `parser_version` | Unique version tuple |

### Methodology

| Table | Key Columns | Constraints |
|---|---|---|
| `route_weights` | `id`, `route_id` FK→routes, `weight`, `effective_from`, `effective_to`, `config_version` | CHECK weight>0, date order |

### Evidence (append-only)

| Table | Key Columns | Constraints |
|---|---|---|
| `fare_raw` | `id` (UUID), `source_id` FK→sources, `collected_at`, `raw_payload` (JSON), `request_metadata` (JSON) | Immutable by convention |

### Observations (processed)

| Table | Key Columns | Constraints |
|---|---|---|
| `fare_observations` | `id` (UUID), `raw_id` FK→fare_raw, `observed_at`, `source_id`, `origin_id`, `destination_id`, `airline_id`, fare components (Numeric(12,2)), `total_payable_fare`, `availability_status`, `quality_status`, `quality_score` | CHECK origin≠dest, advance≥0, monetary≥0, currency len=3, score 0–100 |

Composite indexes: `(observed_at, source_id)`, `(origin_id, destination_id, departure_date)`, `(departure_date, advance_purchase_days)`, `(quality_status)`.

### Outputs

| Table | Key Columns | Constraints |
|---|---|---|
| `index_values` | `id` (UUID), `frequency`, `period_start`, `period_end`, `index_value` (Numeric(12,4)), `config_version`, `calculation_version` | UNIQUE (freq, period_start, config_version) |
| `index_components` | `id` (UUID), `index_value_id` FK→index_values (CASCADE), `route_id` FK→routes, `representative_fare`, `price_relative`, `weight` | — |

## Planned Tables (deferred)

- Operations: `scraping_jobs`, `scraping_runs`, `system_events` (Phase 8/9)
- Quality: `validation_results`, `data_quality`, `anomalies` (Phase 4/9)

## Integrity Rules

- Origin and destination differ and reference valid airports.
- Monetary values are non-negative when present; valid available totals must be positive.
- Unavailable/sold-out/cancelled observations have null payable prices unless a separately evidenced quoted price is explicitly modeled.
- Currency uses a validated ISO code, initially INR.
- Raw observations are immutable; reprocessing creates versioned derived records.
- Weights and methodology records include effective dates and versions.

## Indexing Plan

Composite/individual indexes on observation timestamp/date, route, airline, departure date, advance window, source, processing status, and index frequency/period. Uniqueness constraints for reference identifiers.

## Transactions and Retention

Batch ingestion and pipeline state changes must be transactional. Historical observations are retained by default. Any deletion, partition-drop, or retention policy requires explicit owner approval and documentation.

## Migration Policy

Every schema change uses a reviewed Alembic migration with upgrade/downgrade behavior where safe. Never edit deployed schemas manually or delete migration history without approval.

## ORM Files

- [`backend/app/core/database.py`](file:///c:/Users/abhin/Desktop/AirIndex_India/backend/app/core/database.py) — Base, engine, session
- [`backend/app/models/reference.py`](file:///c:/Users/abhin/Desktop/AirIndex_India/backend/app/models/reference.py) — City, Airport, Airline, Route, Source, SourceConnector
- [`backend/app/models/methodology.py`](file:///c:/Users/abhin/Desktop/AirIndex_India/backend/app/models/methodology.py) — RouteWeight
- [`backend/app/models/evidence.py`](file:///c:/Users/abhin/Desktop/AirIndex_India/backend/app/models/evidence.py) — FareRaw
- [`backend/app/models/observations.py`](file:///c:/Users/abhin/Desktop/AirIndex_India/backend/app/models/observations.py) — FareObservationModel
- [`backend/app/models/outputs.py`](file:///c:/Users/abhin/Desktop/AirIndex_India/backend/app/models/outputs.py) — IndexValue, IndexComponent
