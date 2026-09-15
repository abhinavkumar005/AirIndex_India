/**
 * Backtest / Validation — prototype backtest summary statistics.
 *
 * DGCA reference comparison arrives in Phase 12; for now this shows
 * backtest-style index statistics over a selectable period.
 */

import { useEffect, useState } from 'react'
import type { EChartsOption } from 'echarts'
import EChart from '@/components/EChart'
import { Card, ErrorBanner, Loading, PageHeader, StatTile } from '@/components/ui'
import { api, ApiError } from '@/api/client'
import type { IndexValue, ValidationSummary } from '@/types/api'

function isoDaysAgo(days: number): string {
  const d = new Date()
  d.setDate(d.getDate() - days)
  return d.toISOString().slice(0, 10)
}

export default function Validation() {
  const [summary, setSummary] = useState<ValidationSummary | null>(null)
  const [daily, setDaily] = useState<IndexValue[]>([])
  const [days, setDays] = useState(30)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    async function load() {
      try {
        const start = isoDaysAgo(days - 1)
        const [s, d] = await Promise.all([
          api.getValidationSummary(start, undefined),
          api.getIndexDaily(start, undefined),
        ])
        setSummary(s)
        setDaily(d)
      } catch (e) {
        setError(e instanceof ApiError ? e.message : String(e))
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [days])

  if (loading) return <Loading />
  if (error) return <ErrorBanner message={error} />
  if (!summary) return <ErrorBanner message="No data returned" />

  const option: EChartsOption = {
    title: { text: `Backtest Daily APIx — ${days} days`, left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: daily.map((d) => d.period_start) },
    yAxis: { type: 'value', scale: true },
    series: [
      {
        name: 'APIx',
        type: 'line',
        data: daily.map((d) => d.index_value),
        smooth: true,
        lineStyle: { width: 2, color: '#1e3a5f' },
        itemStyle: { color: '#1e3a5f' },
        connectNulls: true,
        markLine: {
          symbol: 'none',
          data: [
            summary.average_index_value !== null
              ? { yAxis: Number(summary.average_index_value), name: 'mean', lineStyle: { color: '#f57c00', type: 'dashed' as const } }
              : null,
            summary.min_index_value !== null
              ? { yAxis: Number(summary.min_index_value), name: 'min', lineStyle: { color: '#c62828', type: 'dotted' as const } }
              : null,
            summary.max_index_value !== null
              ? { yAxis: Number(summary.max_index_value), name: 'max', lineStyle: { color: '#2e7d32', type: 'dotted' as const } }
              : null,
          ].filter((m): m is NonNullable<typeof m> => m !== null),
        },
      },
    ],
    grid: { left: 50, right: 20, top: 40, bottom: 30 },
  }

  return (
    <div>
      <PageHeader
        title="Backtest / Validation"
        subtitle="Prototype backtest statistics · DGCA reference comparison arrives with Phase 12 (reference data not yet supplied)"
      />

      <div className="mb-4 flex items-center gap-2">
        <label htmlFor="days" className="text-sm font-medium text-gov-600">
          Backtest window:
        </label>
        <select
          id="days"
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="rounded-md border border-gov-300 bg-white px-3 py-1.5 text-sm shadow-sm focus:border-gov-500 focus:outline-none"
        >
          <option value={7}>7 days</option>
          <option value={14}>14 days</option>
          <option value={30}>30 days</option>
          <option value={60}>60 days</option>
        </select>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile
          label="Average APIx"
          value={summary.average_index_value === null ? '—' : Number(summary.average_index_value).toFixed(2)}
        />
        <StatTile
          label="Min / Max"
          value={
            summary.min_index_value === null || summary.max_index_value === null
              ? '—'
              : `${Number(summary.min_index_value).toFixed(2)} / ${Number(summary.max_index_value).toFixed(2)}`
          }
        />
        <StatTile
          label="Average Coverage"
          value={summary.average_coverage_pct === null ? '—' : `${Number(summary.average_coverage_pct).toFixed(1)}%`}
        />
        <StatTile
          label="Total Observations"
          value={String(summary.total_observations)}
          hint={`${summary.backtest_days} days · ${summary.route_count} routes`}
        />
      </div>

      <Card className="mt-4">
        <EChart option={option} height={360} />
      </Card>
    </div>
  )
}
