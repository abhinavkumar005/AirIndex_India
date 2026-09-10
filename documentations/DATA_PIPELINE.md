# Data Pipeline

## Required Stages

```text
Source -> Collection -> Raw Data -> Validation -> Cleaning -> Deduplication
-> Normalization -> Outlier Detection -> Quality Scoring
-> Statistical Aggregation -> Index Construction -> Analytics -> API -> Dashboard
```

## Stage Contracts

- **Collection:** captures source, request/run context, timestamps, versions, and raw evidence.
- **Raw data:** append-only; never overwritten by parsing or cleaning.
- **Validation:** records structural/domain checks and does not silently discard failures.
- **Cleaning:** performs explicit, versioned corrections only when defensible.
- **Deduplication:** links/flags probable duplicates using documented keys and confidence.
- **Normalization:** maps source-specific fields and statuses to canonical types.
- **Outlier detection:** records method, parameters, score, and flag; retains evidence.
- **Quality scoring:** produces a documented prototype status/score and factor breakdown.
- **Aggregation/index:** consumes eligible normalized records, configuration, and calculation versions.
- **Analytics/API/dashboard:** reads published derived products and coverage/provenance metadata.

## Idempotency and Auditability

Jobs must be rerunnable without duplicating logical outputs. Every derived record references its inputs and processing version. Failures record safe diagnostics and can be retried from the last durable stage.

## Availability Treatment

`SOLD_OUT`, `CANCELLED`, `NOT_AVAILABLE`, and `UNKNOWN` are explicit states. They are not converted to a zero fare. Missing components and unavailable totals remain null and are evaluated by validation/quality rules.
