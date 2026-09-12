# Known Issues and Open Inputs

## Requires Official or Owner Input

- Official PSD/MoSPI route basket, weights, base period, aggregation, missing-data, and publication rules are unavailable.
- DGCA reference dataset, granularity, licensing/usage terms, and comparison protocol are not confirmed.
- No airline or OTA has an approved source-access record.
- Deployment environment, availability objective, and administrative identity solution are undecided.

## Prototype Gaps

- Persistence wiring is not implemented: the API computes observations and index values on-the-fly from the mock provider (ADR-007). PostgreSQL tables exist but nothing reads/writes them at runtime yet.
- The index engine collapses the advance-purchase dimension: representative fares are computed per route × period, not per route × period × lead-time cell (STATISTICAL_METHODOLOGY.md defines cells as route, period, and lead-time). The lead-time elasticity dashboard view (Phase 7) will need cell-level output; extending the engine requires owner approval since it changes aggregation granularity.
- The repository layer from the Phase 6 plan was intentionally deferred (ADR-007); it arrives with persistence wiring in Phases 8–9.
- The Phase 3–5 modules live in `backend/app/services/` and `backend/app/index_engine/engine.py` instead of the planned `collectors/` + `data_pipeline/` packages (ADR-007).
- Prototype route configuration uses equal illustrative weights and must not be presented as official.
- Prototype airport and airline reference data are curated seed lists, not exhaustive DGCA registers.
- Docker Compose is intentionally a placeholder until runnable services are defined.
- All work since the Phase 1 commit is uncommitted in the working tree.

## Risk Notes

- Fare component availability varies by source and purchase flow.
- Convenience fees may depend on payment method or checkout stage, complicating like-for-like comparison.
- Dynamic inventory can make observations non-repeatable; timestamping and raw evidence are essential.
