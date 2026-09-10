# Statistical Methodology

## Status and Purpose

This is a **DEMO / PROTOTYPE / ASSUMPTION** methodology for engineering development. It is not official MoSPI, PSD, DGCA, or CPI methodology. Official inputs must replace these settings through versioned configuration after approval.

## Measurement Target

APIx is intended to measure changes in representative payable fares for a configurable basket of Indian domestic routes and advance-purchase windows, while retaining enough provenance to reproduce each result.

## Observation Windows

The initial configurable lead times are T+1, T+7, T+15, T+30, and T+45, calculated from the observation date. They are not individually hard-coded in processing logic.

## Route Basket and Weights

Prototype routes and equal weights may be used only for development and must be visibly labeled. Production/official baskets require PSD methodology and/or approved DGCA traffic data. Weights have effective dates and version identifiers.

## Fare Measure

The preferred observation measure is total payable fare with separately preserved base fare, taxes, airport charges, user-development fee, convenience fee, and other charges. Missing valid prices remain null. Sold-out, cancelled, and unavailable observations are not zero-priced.

## Representative Fare

**Prototype assumption:** use a configurable robust statistic, initially the median of eligible normalized total fares within a route, period, and lead-time cell. Eligibility rules, source treatment, minimum coverage, and fallback behavior must be versioned.

## Price Relative and Aggregation

For an eligible cell:

```text
price_relative = current_representative_fare / base_representative_fare * 100
```

Route and composite indices are weighted aggregations of eligible price relatives. Missing cells are not silently treated as zero. Weight redistribution or carry-forward rules are not yet approved and must be configurable and disclosed.

## Frequency

Daily values are calculated from daily observation cells. Weekly and monthly values will be derived by a documented configurable aggregation of eligible daily values; the precise official convention is unresolved.

## Outliers

Outlier methods may include IQR, MAD, robust z-score, and route-history thresholds. Outliers are flagged with method/version and retained. Exclusion from representative-fare calculation must be explicit and auditable.

## Quality and Exclusions

Quality scoring is a prototype engineering indicator based on completeness, source reliability configuration, parsing confidence, duplicate likelihood, timestamp validity, and anomaly flags. It is not an official government confidence score. Every exclusion records reason and rule version.

## Provenance

Each index value must reference calculation version, configuration version, base period, contributing cells, weights, representative fares, excluded records and reasons, coverage, and creation timestamp.

## Validation

Backtesting will cover at least 30 days when real or clearly labeled reference observations exist. DGCA comparison will evaluate coverage, directional agreement, correlation, and explainable deviations; it will not presume equality with DGCA average fares.

## Unresolved Official Inputs

- Base period and rebasing policy
- Official route basket and weights
- Source selection/weighting
- Representative-fare statistic
- Missing-cell and weight-redistribution treatment
- Weekly/monthly aggregation convention
- Minimum coverage and publication thresholds
