# Development Plan

## Delivery Strategy

Build a vertical, auditable path using synthetic data before integrating external sources:

```text
Mock source -> raw record -> quality pipeline -> index engine -> API -> dashboard
```

## Near-Term Milestones

1. Define typed domain enums/entities and configuration loaders with validation.
2. Design and migrate the relational schema, constraints, and indexes.
3. Generate deterministic mock observations across routes, airlines, windows, components, and availability states.
4. Implement pure, testable pipeline stages with recorded validation outcomes.
5. Implement a configurable index calculation package independent of FastAPI and collectors.
6. Add repositories/services and the versioned read API.
7. Add dashboard views against stable API contracts.

## Definition of Done

A task is done only when code/artifacts exist, relevant automated checks have run, behavior is verified, documentation is synchronized, limitations are recorded, and `PROJECT_STATUS.md` plus `CHANGELOG.md` are current.

## Approval Gates

Owner approval is required before Phase 1 begins and before changes to core architecture, major dependencies, schema architecture, methodology, weights, external-source enablement, deployment architecture, or destructive operations.
