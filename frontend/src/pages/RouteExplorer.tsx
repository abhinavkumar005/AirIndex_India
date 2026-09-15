/**
 * Route Explorer — sector-wise fare heatmap and route trend drill-down.
 *
 * Left: matrix of routes × price relatives (heat). Click a cell to load
 * the route's representative-fare trend (right).
 */

import { useEffect, useMemo, useState } from 'react'
import type { EChartsOption } from 'echarts'
import EChart from '@/components/EChart'
import { Card, ErrorBanner, Loading, PageHeader } from '@/components/ui'
import { api, ApiError } from '@/api/client'
import type { IndexValue, RouteInfo, RouteTrend } from '@/types/api'

function isoDaysAgo(days: number): string {
  const d = new Date()
  d.setDate(d.getDate() - days)
  return d.toISOString().slice(0, 10)
}

export default function RouteExplorer() {
  const [routes, setRoutes] = useState<RouteInfo[]>([])
  const [daily, setDaily] = useState<IndexValue[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [trend, setTrend] = useState<RouteTrend | null>(null)
  const [loading, setLoading] = useState(true)
  const [trendLoading, setTrendLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [trendError, setTrendError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const [r, d] = await Promise.all([
          api.getRoutes(),
          api.getIndexDaily(isoDaysAgo(29), undefined),
        ])
        setRoutes(r)
        setDaily(d)
        if (r.length > 0) setSelected(r[0].code)
      } catch (e) {
        setError(e instanceof ApiError ? e.message : String(e))
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  useEffect(() => {
    if (!selected) return
    setTrendLoading(true)
    setTrendError(null)
    api
      .getRouteTrend(selected, isoDaysAgo(29), undefined)
      .then(setTrend)
      .catch((e) => setTrendError(e instanceof ApiError ? e.message : String(e)))
      .finally(() => setTrendLoading(false))
  }, [selected])

  // Build route × date matrix of price relatives from daily index components
  const heatData = useMemo(() => {
    const dates = daily.map((d) => d.period_start)
    const rows: { route: string; values: (number | null)[] }[] = []
    for (const route of routes) {
      const values = daily.map((d) => {
        const comp = d.route_components.find((c) => c.route_code === route.code)
        return comp?.price_relative ?? null
      })
      rows.push({ route: route.code, values })
    }
    return { dates, rows }
  }, [routes, daily])

  if (loading) return <Loading />
  if (error) return <ErrorBanner message={error} />

  const heatOption: EChartsOption = {
    title: { text: 'Route Price Relatives by Day (30 days)', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: {
      position: 'top',
      formatter: (params: any) =>
        `${heatData.rows[params.value[1]].route}<br/>${heatData.dates[params.value[0]]}: <b>${Number(params.value[2]).toFixed(1)}</b>`,
    },
    grid: { left: 90, right: 20, top: 40, bottom: 60 },
    xAxis: { type: 'category', data: heatData.dates, axisLabel: { rotate: 45, fontSize: 10 } },
    yAxis: { type: 'category', data: heatData.rows.map((r) => r.route) },
    visualMap: {
      min: 90,
      max: 115,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      inRange: { color: ['#d1dae8', '#7b95b6', '#1e3a5f'] },
    },
    series: [
      {
        type: 'heatmap',
        data: heatData.rows.flatMap((row, yi) =>
          row.values.map((v, xi) => (v === null ? null : [xi, yi, v])).filter((x) => x !== null),
        ),
        label: { show: false },
        emphasis: { itemStyle: { shadowBlur: 4, shadowColor: 'rgba(0,0,0,0.3)' } },
      },
    ],
  }

  const trendOption: EChartsOption = {
    title: {
      text: selected ? `${selected} — Representative Fare (30 days)` : 'Route Trend',
      left: 'center',
      textStyle: { fontSize: 14 },
    },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: trend?.trend.map((t) => t.date) ?? [] },
    yAxis: { type: 'value', scale: true, name: 'INR' },
    series: [
      {
        name: 'Representative fare',
        type: 'line',
        data: trend?.trend.map((t) => t.representative_fare) ?? [],
        smooth: true,
        lineStyle: { width: 2, color: '#1e3a5f' },
        itemStyle: { color: '#1e3a5f' },
        connectNulls: true,
      },
    ],
    grid: { left: 60, right: 20, top: 40, bottom: 30 },
  }

  return (
    <div>
      <PageHeader
        title="Route Explorer"
        subtitle="Sector-wise price relatives and representative fares · equal illustrative weights (prototype)"
      />

      <div className="mb-4 flex flex-wrap items-center gap-2">
        <label htmlFor="route-select" className="text-sm font-medium text-gov-600">
          Route:
        </label>
        <select
          id="route-select"
          value={selected ?? ''}
          onChange={(e) => setSelected(e.target.value)}
          className="rounded-md border border-gov-300 bg-white px-3 py-1.5 text-sm shadow-sm focus:border-gov-500 focus:outline-none"
        >
          {routes.map((r) => (
            <option key={r.code} value={r.code}>
              {r.code} (weight {(r.weight * 100).toFixed(2)}%)
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 gap-4">
        <Card>
          <EChart option={heatOption} height={320} />
        </Card>
        <Card>
          {trendLoading ? (
            <Loading />
          ) : trendError ? (
            <ErrorBanner message={trendError} />
          ) : (
            <EChart option={trendOption} height={300} />
          )}
        </Card>
      </div>
    </div>
  )
}
