/**
 * Lead-Time Elasticity — advance-purchase window curves (T+1 … T+45).
 *
 * One line per route: representative fare vs days-before-departure.
 */

import { useEffect, useMemo, useState } from 'react'
import type { EChartsOption } from 'echarts'
import EChart from '@/components/EChart'
import { Card, ErrorBanner, Loading, PageHeader, StatTile } from '@/components/ui'
import { api, ApiError } from '@/api/client'
import type { LeadTimeElasticity } from '@/types/api'

const ROUTE_COLORS = [
  '#1e3a5f', '#f57c00', '#2e7d32', '#7b1fa2', '#c62828', '#00838f',
]

export default function LeadTimeElasticity() {
  const [data, setData] = useState<LeadTimeElasticity | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .getLeadTimeElasticity()
      .then(setData)
      .catch((e) => setError(e instanceof ApiError ? e.message : String(e)))
      .finally(() => setLoading(false))
  }, [])

  // Group cells by route
  const byRoute = useMemo(() => {
    if (!data) return new Map<string, Map<number, number>>()
    const map = new Map<string, Map<number, number>>()
    for (const cell of data.routes) {
      if (cell.representative_fare === null) continue
      if (!map.has(cell.route_code)) map.set(cell.route_code, new Map())
      map.get(cell.route_code)!.set(cell.advance_days, Number(cell.representative_fare))
    }
    return map
  }, [data])

  if (loading) return <Loading />
  if (error) return <ErrorBanner message={error} />
  if (!data) return <ErrorBanner message="No data returned" />

  const option: EChartsOption = {
    title: {
      text: `Representative Fare by Advance-Purchase Window — ${data.observation_date}`,
      left: 'center',
      textStyle: { fontSize: 14 },
    },
    tooltip: { trigger: 'axis', valueFormatter: (v) => `₹${Number(v).toFixed(0)}` },
    legend: { bottom: 0, type: 'scroll' },
    xAxis: {
      type: 'category',
      name: 'Days before departure',
      data: data.advance_windows.map((w) => `T+${w}`),
    },
    yAxis: { type: 'value', scale: true, name: 'INR' },
    series: Array.from(byRoute.entries()).map(([route, fares], i) => ({
      name: route,
      type: 'line' as const,
      data: data.advance_windows.map((w) => fares.get(w) ?? null),
      smooth: true,
      lineStyle: { width: 2 },
      itemStyle: { color: ROUTE_COLORS[i % ROUTE_COLORS.length] },
      connectNulls: true,
    })),
    grid: { left: 60, right: 20, top: 40, bottom: 60 },
  }

  // Average T+1 premium over T+45 per route
  const premiums = Array.from(byRoute.entries())
    .map(([route, fares]) => {
      const t1 = fares.get(1)
      const t45 = fares.get(45)
      return t1 && t45 ? { route, premium: ((t1 - t45) / t45) * 100 } : null
    })
    .filter((p): p is { route: string; premium: number } => p !== null)

  const avgPremium =
    premiums.length > 0 ? premiums.reduce((s, p) => s + p.premium, 0) / premiums.length : null

  const premiumOption: EChartsOption = {
    title: { text: 'T+1 Premium vs T+45 (%)', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: premiums.map((p) => p.route), axisLabel: { rotate: 30 } },
    yAxis: { type: 'value', name: '%' },
    series: [
      {
        type: 'bar',
        data: premiums.map((p) => Number(p.premium.toFixed(1))),
        itemStyle: { color: '#f57c00' },
      },
    ],
    grid: { left: 50, right: 20, top: 40, bottom: 50 },
  }

  return (
    <div>
      <PageHeader
        title="Lead-Time Elasticity"
        subtitle="How representative fares scale with advance-purchase window · statistic: median of eligible observations"
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatTile
          label="Average T+1 Premium"
          value={avgPremium === null ? '—' : `${avgPremium.toFixed(1)}%`}
          tone={avgPremium !== null && avgPremium > 0 ? 'up' : 'flat'}
          hint="across routes with T+1 and T+45 fares"
        />
        <StatTile label="Windows" value={data.advance_windows.map((w) => `T+${w}`).join(' · ')} />
        <StatTile
          label="Cells with Fares"
          value={`${byRoute.size * data.advance_windows.length - data.routes.filter((c) => c.representative_fare === null).length} / ${data.routes.length}`}
        />
    </div>

      <div className="mt-4 grid grid-cols-1 gap-4">
        <Card>
          <EChart option={option} height={380} />
        </Card>
        <Card>
          <EChart option={premiumOption} height={280} />
        </Card>
      </div>
    </div>
  )
}
