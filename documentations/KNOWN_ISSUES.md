# Known Issues and Open Inputs

## Requires Official or Owner Input

- Official PSD/MoSPI route basket, weights, base period, aggregation, missing-data, and publication rules are unavailable.
- DGCA reference dataset, granularity, licensing/usage terms, and comparison protocol are not confirmed.
- No airline or OTA has an approved source-access record.
- Deployment environment, availability objective, and administrative identity solution are undecided.

## Prototype Gaps

- No database migration, collector, pipeline, index engine, API, frontend, scheduler, or automated integration/e2e test suite exists yet.
- Domain models and configuration loaders are implemented; the next step is the PostgreSQL schema (Phase 2).
- Prototype route configuration uses equal illustrative weights and must not be presented as official.
- Prototype airport and airline reference data are curated seed lists, not exhaustive DGCA registers.
- Docker Compose is intentionally a placeholder until runnable services are defined.

## Risk Notes

- Fare component availability varies by source and purchase flow.
- Convenience fees may depend on payment method or checkout stage, complicating like-for-like comparison.
- Dynamic inventory can make observations non-repeatable; timestamping and raw evidence are essential.
