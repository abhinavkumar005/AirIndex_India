# Data Dictionary

This initial dictionary documents planned core fields. It must be synchronized with the implemented schema during Phase 1 and Phase 2.

## Fare Observation Core

| Field | Type | Nullable | Meaning / Allowed Values | Source / Transformation | Example |
|---|---|---:|---|---|---|
| observation_id | UUID | No | Stable observation identifier | Generated at ingestion | `018f...` |
| observed_at | timezone datetime | No | Collection timestamp in UTC | Collector clock | `2026-09-07T06:30:00Z` |
| source_code | string | No | Configured source identifier | Source adapter | `MOCK_AIRLINE` |
| source_type | enum | No | `AIRLINE`, `OTA`, `FEED`, `MOCK` | Source configuration | `MOCK` |
| origin_airport | char(3) | No | Valid IATA airport code | Parsed and reference-validated | `DEL` |
| destination_airport | char(3) | No | Valid IATA airport code; differs from origin | Parsed and validated | `BOM` |
| origin_city | string | No | Reference city name/code | Airport lookup | `Delhi` |
| destination_city | string | No | Reference city name/code | Airport lookup | `Mumbai` |
| departure_date | date | No | Scheduled local departure date | Source result | `2026-09-14` |
| departure_time | timezone/local datetime | Yes | Scheduled departure timestamp with time context | Source result | `2026-09-14T08:00:00+05:30` |
| arrival_time | timezone/local datetime | Yes | Scheduled arrival timestamp | Source result | `2026-09-14T10:10:00+05:30` |
| airline_code | string | Yes | Valid configured carrier code | Parsed/reference lookup | `6E` |
| airline_name | string | Yes | Display name at observation time | Reference lookup | `IndiGo` |
| flight_number | string | Yes | Marketing flight identifier | Source result | `6E 123` |
| fare_class | string | Yes | Source-provided or normalized fare class | Parser | `ECONOMY` |
| advance_purchase_days | integer | No | Departure date minus observation date | Derived | `7` |
| base_fare | decimal | Yes | Base fare in currency units | Parsed | `4200.00` |
| taxes | decimal | Yes | Tax component | Parsed | `310.00` |
| airport_charges | decimal | Yes | Airport charge component | Parsed | `150.00` |
| user_development_fee | decimal | Yes | UDF component | Parsed | `80.00` |
| convenience_fee | decimal | Yes | Booking/convenience fee | Parsed | `199.00` |
| other_charges | decimal | Yes | Other identified charges | Parsed | `0.00` |
| total_payable_fare | decimal | Yes | Payable price; null unless valid and available | Parsed/validated | `4939.00` |
| currency | char(3) | No | ISO 4217 code | Source/default validated | `INR` |
| availability_status | enum | No | `AVAILABLE`, `SOLD_OUT`, `CANCELLED`, `NOT_AVAILABLE`, `UNKNOWN` | Normalization | `AVAILABLE` |
| cancellation_status | enum | No | `ACTIVE`, `CANCELLED`, `UNKNOWN` | Normalization | `ACTIVE` |
| raw_reference | JSON/reference | No | Payload location, request metadata, or permitted source reference | Ingestion | `{...}` |
| connector_version | string | No | Adapter build/version | Runtime metadata | `mock-0.1.0` |
| parser_version | string | No | Parser/rule version | Runtime metadata | `mock-0.1.0` |
| quality_status | enum | No | `PENDING`, `VALID`, `FLAGGED`, `INVALID` | Quality pipeline | `PENDING` |
| quality_score | decimal | Yes | Prototype score from 0 to 100 | Quality pipeline | `94.5` |

## Planned Reference and Derived Entities

Airports, cities, airlines, routes, sources, connectors, jobs, runs, raw fares, normalized observations, fare components, validation results, quality findings, anomalies, route weights, index values, index components, and system events are described structurally in `DATABASE.md`. Exact implemented fields will be added here with constraints and transformation rules during schema work.
