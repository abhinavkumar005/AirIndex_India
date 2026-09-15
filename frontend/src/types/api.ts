/**
 * TypeScript types mirroring the backend API response schemas
 * (backend/app/schemas/responses.py).
 *
 * Decimal fields arrive as JSON numbers/strings; parsed as `number | null`.
 */

export interface ApiMeta {
  generated_at: string
  version: string
  pagination: PaginationMeta | null
}

export interface PaginationMeta {
  total: number
  page: number
  per_page: number
  total_pages: number
}

export interface ApiEnvelope<T> {
  data: T
  meta: ApiMeta
}

// ---------------------------------------------------------------------------
// Index
// ---------------------------------------------------------------------------

export interface RouteComponent {
  route_code: string
  representative_fare: number | null
  base_fare: number | null
  price_relative: number | null
  weight: number
  weighted_contribution: number | null
  observation_count: number
  excluded_count: number
  is_eligible: boolean
  ineligibility_reason: string | null
}

export interface IndexValue {
  frequency: 'daily' | 'weekly' | 'monthly'
  period_start: string
  period_end: string
  index_value: number | null
  base_period: string | null
  config_version: string
  calculation_version: string
  coverage_pct: number
  route_count: number
  eligible_route_count: number
  observation_count: number
  route_components: RouteComponent[]
}

export interface CurrentIndex {
  index_value: number | null
  frequency: string
  as_of: string
  coverage_pct: number
  route_count: number
  eligible_route_count: number
  observation_count: number
  config_version: string
  calculation_version: string
  trend_7d: number | null
  trend_30d: number | null
}

export interface LeadTimeCell {
  route_code: string
  observation_date: string
  advance_days: number
  observation_count: number
  excluded_count: number
  representative_fare: number | null
  statistic_used: string
}

export interface LeadTimeElasticity {
  observation_date: string
  advance_windows: number[]
  routes: LeadTimeCell[]
}

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

export interface RouteInfo {
  code: string
  origin: string
  destination: string
  weight: number
  effective_from: string
  effective_to: string | null
}

export interface RouteTrendPoint {
  date: string
  representative_fare: number | null
  price_relative: number | null
  observation_count: number
}

export interface RouteTrend {
  route_code: string
  origin: string
  destination: string
  trend: RouteTrendPoint[]
}

// ---------------------------------------------------------------------------
// Fares
// ---------------------------------------------------------------------------

export interface FareObservation {
  observation_id: string
  observed_at: string
  source_code: string
  source_type: string
  origin_airport: string
  destination_airport: string
  departure_date: string
  airline_code: string | null
  airline_name: string | null
  flight_number: string | null
  fare_class: string | null
  advance_purchase_days: number
  base_fare: number | null
  taxes: number | null
  airport_charges: number | null
  user_development_fee: number | null
  convenience_fee: number | null
  other_charges: number | null
  total_payable_fare: number | null
  currency: string
  availability_status: string
  quality_status: string
  quality_score: number | null
}

// ---------------------------------------------------------------------------
// Sources & Quality
// ---------------------------------------------------------------------------

export interface SourceStatus {
  code: string
  source_type: string
  enabled: boolean
  compliance_status: string
  rate_limit_per_minute: number | null
  last_collection_at: string | null
  observations_24h: number
  health: string
}

export interface QualitySummary {
  period_start: string
  period_end: string
  total_observations: number
  valid_count: number
  flagged_count: number
  invalid_count: number
  outlier_count: number
  duplicate_count: number
  average_quality_score: number | null
  coverage_by_route: Record<string, number>
  coverage_by_source: Record<string, number>
}

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

export interface ValidationSummary {
  period_start: string
  period_end: string
  backtest_days: number
  average_index_value: number | null
  min_index_value: number | null
  max_index_value: number | null
  average_coverage_pct: number | null
  route_count: number
  total_observations: number
  status: string
}
