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
