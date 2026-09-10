# Database Design

## Status

PLANNED. No database, models, or migrations exist yet.

## Platform

PostgreSQL is the system of record. TimescaleDB is optional and will be enabled only when measured time-series benefits justify it. SQLAlchemy models and Alembic migrations will control schema evolution.

## Planned Tables

- Reference: `cities`, `airports`, `airlines`, `routes`, `sources`, `source_connectors`
- Operations: `scraping_jobs`, `scraping_runs`, `system_events`
- Evidence: `fare_raw` (append-only payload/reference and collection metadata)
- Processed data: `fare_observations`, `fare_components`, `validation_results`, `data_quality`, `anomalies`
- Methodology: `route_weights`, calculation/configuration versions
- Outputs: `index_values`, `index_components`

Tables will only be introduced when they enforce a real domain, audit, or query requirement.

## Integrity Rules

- Origin and destination differ and reference valid airports.
- Monetary values are non-negative when present; valid available totals must be positive.
- Unavailable/sold-out/cancelled observations have null payable prices unless a separately evidenced quoted price is explicitly modeled.
- Currency uses a validated ISO code, initially INR.
- Raw observations are immutable; reprocessing creates versioned derived records.
- Weights and methodology records include effective dates and versions.

## Indexing Plan

Use composite/individual indexes guided by queries on observation timestamp/date, route, airline, departure date, advance window, source, processing status, and index frequency/period. Add uniqueness constraints for reference identifiers and carefully defined deduplication keys; do not confuse likely duplicates with database identity.

## Transactions and Retention

Batch ingestion and pipeline state changes must be transactional. Historical observations are retained by default. Any deletion, partition-drop, or retention policy requires explicit owner approval and documentation.

## Migration Policy

Every schema change uses a reviewed Alembic migration with upgrade/downgrade behavior where safe. Never edit deployed schemas manually or delete migration history without approval.
