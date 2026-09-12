# Architecture Decision Log

## ADR-001 — Modular Monorepo

**Date:** 2026-09-07  
**Decision:** Use a modular monorepo with separate logical API, worker, scheduler, processing, collector, and frontend boundaries.  
**Context:** The SIH prototype needs fast integrated development without losing separation of concerns.  
**Alternatives:** Independent microservices; single undifferentiated application.  
**Reason:** A modular monorepo minimizes operational complexity while preserving future extraction points.  
**Consequences:** Shared releases are simpler; module boundaries must be enforced through code structure and tests.

## ADR-002 — PostgreSQL as System of Record

**Date:** 2026-09-07  
**Decision:** Plan PostgreSQL as the relational system of record, with TimescaleDB capabilities optional where beneficial.  
**Context:** Observations, provenance, reference data, weights, and index components have relational and time-series access patterns.  
**Alternatives:** MongoDB; files as the primary store; mandatory TimescaleDB.  
**Reason:** PostgreSQL provides transactions, constraints, indexing, JSON support, and mature migrations without requiring an extension.  
**Consequences:** Schema changes require Alembic migrations; time-series optimization remains evidence-driven.

## ADR-003 — Immutable Raw Layer

**Date:** 2026-09-07  
**Decision:** Preserve raw observations and payload references as append-only records; corrections create derived/versioned records.  
**Context:** Statistical outputs must be reproducible and auditable.  
**Alternatives:** Overwrite observations after cleaning; store normalized data only.  
**Reason:** Auditability and parser reprocessing require original evidence.  
**Consequences:** Storage use is higher and retention changes require explicit approval.

## ADR-004 — Configuration-Driven Prototype Methodology

**Date:** 2026-09-07  
**Decision:** Keep route baskets, weights, base period, aggregation rules, and advance windows configurable and versioned. Label initial values as prototype assumptions.  
**Context:** Official PSD/MoSPI methodology is not yet available.  
**Alternatives:** Hard-code assumed weights; block all development.  
**Reason:** Configuration enables development without misrepresenting assumptions as official.  
**Consequences:** Outputs must expose methodology/configuration versions and cannot be called official CPI measures.

## ADR-005 — Compliance Gate Before Real Collection

**Date:** 2026-09-07  
**Decision:** Disable real-source collection until source authorization and policy checks are recorded; use mock/authorized data first.  
**Context:** Source access permissions are unknown and security bypass is prohibited.  
**Alternatives:** Scrape first and assess later; omit external collection entirely.  
**Reason:** Compliance is a functional prerequisite, while a mock provider prevents blocked product development.  
**Consequences:** Initial demonstrations use clearly labeled synthetic data.

## ADR-006 — Deferred Operational Tables

**Date:** 2026-09-11  
**Decision:** Phase 2 implements core domain tables (reference, evidence, observations, methodology, outputs) but defers operational tables (`scraping_jobs`, `scraping_runs`, `system_events`, `validation_results`, `data_quality`, `anomalies`) to later phases.  
**Context:** DATABASE.md lists all planned tables. Phase 2 creates those needed for Phase 3 (mock generator) and Phase 5 (index engine) to read/write data immediately. Operational tables require the pipeline and worker architecture from Phases 4/8/9.  
**Alternatives:** Create all tables upfront with empty usage; create each table only when first referenced.  
**Reason:** "Tables will only be introduced when they enforce a real domain, audit, or query requirement" (DATABASE.md). Creating unused tables adds migration debt without benefit.  
**Consequences:** Later phases will add Alembic migrations for new tables as needed.

## ADR-007 — On-the-Fly Prototype Computation and Consolidated Module Placement

**Date:** 2026-09-12  
**Decision:** Phase 6 API services compute observations and index values on-the-fly from the deterministic mock provider per request, without a repository/DB read path, and the Phase 3–5 modules live in `backend/app/services/` + `backend/app/index_engine/engine.py` rather than the implementation plan's `collectors/` + `data_pipeline/` multi-module layout.  
**Context:** The prototype needs a working end-to-end API before the adapter framework (Phase 8) and workers (Phase 9) exist; the ORM schema (Phase 2) is ready but no ingestion path writes to it yet. A single-file pipeline/engine keeps the prototype navigable.  
**Alternatives:** Build the repository layer querying PostgreSQL now (requires an ingestion + persistence path that doesn't exist yet); split modules exactly per plan layout.  
**Reason:** Requests against the seeded, deterministic mock generator are reproducible and fast enough for a prototype demo; the plan's module boundaries remain the target for Phases 8–9 when collectors, persistence, and workers land.  
**Consequences:** API responses are recomputed per request (no persisted index history yet); moving pipeline/collector code into `collectors/` + `data_pipeline/` packages is deferred work recorded in the roadmap; the repository pattern will be introduced with the persistence wiring. Statistical outputs remain labeled prototype assumptions.

## ADR-008 — First-Observation Base-Period Fallback

**Date:** 2026-09-12  
**Decision:** With `index.yml: base_period: null` (official base period unavailable), index series anchor on their first observation: the anchor day's index is ~100 and subsequent days are computed against the anchor day's representative fares. `/api/v1/index/current` anchors 30 days back so 7-day and 30-day trends share one base. Every result discloses its base via `base_period`.  
**Context:** The engine previously self-based each day (base = current fare), making every index value trivially 100 and all trends 0 — meaningless output. The implementation plan's Phase 5 specified a "configurable first-observation fallback for prototype" that had not been wired into the service layer.  
**Alternatives:** Block index publication until an official base period exists; hard-code a fixed base date.  
**Reason:** The fallback keeps within-series movements meaningful while remaining clearly labeled and reversible via configuration when official inputs arrive.  
**Consequences:** Index levels are comparable within a series but not across requests with different date ranges; results carry `base_period: "first_observation:<date>"` for disclosure. Replacing the fallback with an official base period is a configuration change plus owner approval, not a code change.
