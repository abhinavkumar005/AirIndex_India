/**
 * APIx Overview — main dashboard view.
 *
 * Current composite index, 7d/30d trends, daily/weekly/monthly series,
 * and coverage statistics.
 */

import { useEffect, useState } from 'react'
import type { EChartsOption } from 'echarts'
import EChart from '@/components/EChart'
import { Card, ErrorBanner, Loading, PageHeader, StatTile } from '@/components/ui'
import { api, ApiError } from '@/api/client'
import type { CurrentIndex, IndexValue } from '@/types/api'

function isoDaysAgo(days: number): string {
  const d = new Date()
  d.setDate(d.getDate() - days)
  return d.toISOString().slice(0, 10)
}

export default function Dashboard() {
  const [current, setCurrent] = useState<CurrentIndex | null>(null)
  const [daily, setDaily] = useState<IndexValue[]>([])
  const [weekly, setWeekly] = useState<IndexValue[]>([])
  const [monthly, setMonthly] = useState<IndexValue[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const [cur, d, w, m] = await Promise.all([
          api.getCurrentIndex(),
          api.getIndexDaily(isoDaysAgo(29), undefined),
          api.getIndexWeekly(isoDaysAgo(89), undefined),
          api.getIndexMonthly(isoDaysAgo(179), undefined),
        ])
        setCurrent(cur)
        setDaily(d)
        setWeekly(w)
        setMonthly(m)
      } catch (e) {
        setError(e instanceof ApiError ? e.message : String(e))
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <Loading />
  if (error) return <ErrorBanner message={error} />
  if (!current) return <ErrorBanner message="No data returned" />

  const trendTone = (t: number | null) =>
    t === null ? 'flat' : t > 0 ? 'up' : t < 0 ? 'down' : 'flat'
  const trendText = (t: number | null) =>
    t === null ? '—' : `${t > 0 ? '+' : ''}${Number(t).toFixed(2)}`

  const dailyOption: EChartsOption = {
    title: { text: 'Daily APIx (30 days)', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: daily.map((d) => d.period_start) },
    yAxis: { type: 'value', scale: true },
    series: [
      {
        name: 'APIx',
        type: 'line',
        data: daily.map((d) => d.index_value),
        smooth: true,
        symbolSize: 4,
        lineStyle: { width: 2, color: '#1e3a5f' },
        itemStyle: { color: '#1e3a5f' },
        areaStyle: { opacity: 0.08, color: '#1e3a5f' },
        connectNulls: true,
      },
    ],
    grid: { left: 50, right: 20, top: 40, bottom: 30 },
  }

  const freqOption = (title: string, series: IndexValue[]): EChartsOption => ({
    title: { text: title, left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: series.map((s) => s.period_start) },
    yAxis: { type: 'value', scale: true },
    series: [
      {
        name: 'APIx',
        type: 'line',
        data: series.map((s) => s.index_value),
        smooth: true,
        symbol: 'circle',
        symbolSize: 5,
        lineStyle: { width: 2, color: '#f57c00' },
        itemStyle: { color: '#f57c00' },
        connectNulls: true,
      },
    ],
    grid: { left: 50, right: 20, top: 40, bottom: 30 },
  })

  return (
    <div>
      <PageHeader
        title="APIx Overview"
        subtitle={`Composite airfare price index as of ${current.as_of} · base anchor: first observation of each series`}
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile
          label="Current APIx"
          value={current.index_value === null ? '—' : Number(current.index_value).toFixed(2)}
          hint={`${current.frequency} frequency`}
        />
        <StatTile
          label="7-Day Trend"
          value={trendText(current.trend_7d)}
          tone={trendTone(current.trend_7d)}
          hint="index points vs 7 days ago"
        />
        <StatTile
          label="30-Day Trend"
          value={trendText(current.trend_30d)}
          tone={trendTone(current.trend_30d)}
          hint="index points vs 30-day anchor (=100)"
        />
        <StatTile
          label="Route Coverage"
          value={`${Number(current.coverage_pct).toFixed(1)}%`}
          hint={`${current.eligible_route_count} of ${current.route_count} routes eligible`}
        />
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4">
        <Card>
          <EChart option={dailyOption} height={340} />
        </Card>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <EChart option={freqOption('Weekly APIx (90 days)', weekly)} height={280} />
        </Card>
        <Card>
          <EChart option={freqOption('Monthly APIx (180 days)', monthly)} height={280} />
        </Card>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatTile label="Observations (latest day)" value={String(current.observation_count)} />
        <StatTile label="Config Version" value={current.config_version} />
        <StatTile label="Calculation Version" value={current.calculation_version} />
      </div>
    </div>
  )
}
