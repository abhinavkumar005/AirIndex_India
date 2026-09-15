/**
 * Typed API client for the AirIndex India backend (/api/v1).
 *
 * In dev, Vite proxies /api to http://localhost:8000 (see vite.config.ts),
 * so relative URLs work without CORS setup.
 */

import type {
  ApiEnvelope,
  CurrentIndex,
  FareObservation,
  IndexValue,
  LeadTimeElasticity,
  PaginationMeta,
  QualitySummary,
  RouteInfo,
  RouteTrend,
  SourceStatus,
  ValidationSummary,
} from '@/types/api'

const BASE = '/api/v1'

export class ApiError extends Error {
  status: number
  code: string
  requestId: string | null

  constructor(status: number, code: string, message: string, requestId: string | null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.requestId = requestId
  }
}

async function get<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
  const url = new URL(path, window.location.origin)
  url.pathname = `${BASE}${path}`
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && v !== '') {
        url.searchParams.set(k, String(v))
      }
    }
  }

  const response = await fetch(url.toString())
  if (!response.ok) {
    let code = 'UNKNOWN'
    let message = `Request failed: ${response.status} ${response.statusText}`
    let requestId: string | null = null
    try {
      const body = await response.json()
      code = body.code ?? code
      message = body.message ?? message
      requestId = body.request_id ?? null
    } catch {
      // Non-JSON error body
    }
    throw new ApiError(response.status, code, message, requestId)
  }

  const envelope: ApiEnvelope<T> = await response.json()
  return envelope.data
}

/** GET that returns the full envelope (data + pagination meta). */
async function getEnvelope<T>(
  path: string,
  params?: Record<string, string | number | undefined>,
): Promise<ApiEnvelope<T>> {
  const url = new URL(path, window.location.origin)
  url.pathname = `${BASE}${path}`
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && v !== '') {
        url.searchParams.set(k, String(v))
      }
    }
  }

  const response = await fetch(url.toString())
  if (!response.ok) {
    let code = 'UNKNOWN'
    let message = `Request failed: ${response.status} ${response.statusText}`
    let requestId: string | null = null
    try {
      const body = await response.json()
      code = body.code ?? code
      message = body.message ?? message
      requestId = body.request_id ?? null
    } catch {
      // Non-JSON error body
    }
    throw new ApiError(response.status, code, message, requestId)
  }

  return response.json()
}

// ---------------------------------------------------------------------------
// Endpoints
// ---------------------------------------------------------------------------

export const api = {
  getCurrentIndex(): Promise<CurrentIndex> {
    return get<CurrentIndex>('/index/current')
  },

  getIndexDaily(start?: string, end?: string): Promise<IndexValue[]> {
    return get<IndexValue[]>('/index/daily', { start_date: start, end_date: end })
  },

  getIndexWeekly(start?: string, end?: string): Promise<IndexValue[]> {
    return get<IndexValue[]>('/index/weekly', { start_date: start, end_date: end })
  },

  getIndexMonthly(start?: string, end?: string): Promise<IndexValue[]> {
    return get<IndexValue[]>('/index/monthly', { start_date: start, end_date: end })
  },

  getLeadTimeElasticity(observationDate?: string): Promise<LeadTimeElasticity> {
    return get<LeadTimeElasticity>('/index/lead-time', { observation_date: observationDate })
  },

  getRoutes(): Promise<RouteInfo[]> {
    return get<RouteInfo[]>('/routes')
  },

  getRouteTrend(routeCode: string, start?: string, end?: string): Promise<RouteTrend> {
    return get<RouteTrend>(`/routes/${routeCode}/trend`, { start_date: start, end_date: end })
  },

  getFares(params: {
    observation_date?: string
    route?: string
    airline?: string
    page?: number
    per_page?: number
  }): Promise<{ data: FareObservation[]; pagination: PaginationMeta }> {
    return getEnvelope<FareObservation[]>('/fares', params).then((envelope) => ({
      data: envelope.data,
      pagination: envelope.meta.pagination ?? {
        total: envelope.data.length, page: 1, per_page: envelope.data.length, total_pages: 1,
      },
    }))
  },

  getSourcesStatus(): Promise<SourceStatus[]> {
    return get<SourceStatus[]>('/sources/status')
  },

  getQualitySummary(start?: string, end?: string): Promise<QualitySummary> {
    return get<QualitySummary>('/data-quality', { start_date: start, end_date: end })
  },

  getValidationSummary(start?: string, end?: string): Promise<ValidationSummary> {
    return get<ValidationSummary>('/validation', { start_date: start, end_date: end })
  },
}
