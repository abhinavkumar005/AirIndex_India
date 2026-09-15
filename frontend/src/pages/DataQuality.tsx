/**
 * Data Quality Monitor — coverage metrics, quality distribution, source health.
 */

import { useEffect, useState } from 'react'
import type { EChartsOption } from 'echarts'
import EChart from '@/components/EChart'
import { Card, ErrorBanner, Loading, PageHeader, StatTile } from '@/components/ui'
import { api, ApiError } from '@/api/client'
import type { QualitySummary, SourceStatus } from '@/types/api'

export default function DataQuality() {
  const [quality, setQuality] = useState<QualitySummary | null>(null)
  const [sources, setSources] = useState<SourceStatus[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const [q, s] = await Promise.all([
          api.getQualitySummary(),
          api.getSourcesStatus(),
        ])
        setQuality(q)
        setSources(s)
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
  if (!quality) return <ErrorBanner message="No data returned" />

  const pieOption: EChartsOption = {
    title: { text: 'Observation Disposition', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'item' },
    legend: { bottom: 0 },
    series: [
      {
        type: 'pie',
        radius: ['40%', '65%'],
        label: { formatter: '{b}: {c} ({d}%)' },
        data: [
          { name: 'Valid', value: quality.valid_count, itemStyle: { color: '#2e7d32' } },
          { name: 'Flagged', value: quality.flagged_count, itemStyle: { color: '#f57c00' } },
          { name: 'Invalid', value: quality.invalid_count, itemStyle: { color: '#c62828' } },
        ],
      },
    ],
  }

  const coverageOption: EChartsOption = {
    title: { text: 'Observations by Route', left: 'center', textStyle: { fontSize: 14 } },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: Object.keys(quality.coverage_by_route),
      axisLabel: { rotate: 30 },
    },
    yAxis: { type: 'value' },
    series: [
      {
        type: 'bar',
        data: Object.values(quality.coverage_by_route),
        itemStyle: { color: '#1e3a5f' },
      },
    ],
    grid: { left: 50, right: 20, top: 40, bottom: 60 },
  }

  const sourceHealthColor = (health: string) =>
    health === 'healthy' ? 'bg-emerald-100 text-emerald-800' :
    health === 'disabled' ? 'bg-gov-100 text-gov-600' :
    'bg-red-100 text-red-800'

  const complianceColor = (status: string) =>
    status === 'APPROVED_FOR_SYNTHETIC_DEVELOPMENT' ? 'bg-sky-100 text-sky-800' :
    status === 'APPROVED' ? 'bg-emerald-100 text-emerald-800' :
    'bg-amber-100 text-amber-800'

  return (
    <div>
      <PageHeader
        title="Data Quality Monitor"
        subtitle={`Coverage and quality for ${quality.period_start} · prototype engineering indicator, not an official confidence score`}
      />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile label="Total Observations" value={String(quality.total_observations)} />
        <StatTile
          label="Average Quality Score"
          value={quality.average_quality_score === null ? '—' : Number(quality.average_quality_score).toFixed(1)}
          hint="0–100 composite"
        />
        <StatTile
          label="Outliers Flagged"
          value={String(quality.outlier_count)}
          hint="IQR method, flag-only"
        />
        <StatTile label="Duplicates Removed" value={String(quality.duplicate_count)} />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <EChart option={pieOption} height={300} />
        </Card>
        <Card>
          <EChart option={coverageOption} height={300} />
        </Card>
      </div>

      <Card title="Source Health & Compliance" className="mt-4">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gov-200 text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-gov-500">
                <th className="py-2 pr-4">Source</th>
                <th className="py-2 pr-4">Type</th>
                <th className="py-2 pr-4">Enabled</th>
                <th className="py-2 pr-4">Compliance</th>
                <th className="py-2 pr-4">Rate Limit</th>
                <th className="py-2">Health</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gov-100">
              {sources.map((s) => (
                <tr key={s.code}>
                  <td className="py-2 pr-4 font-medium text-gov-700">{s.code}</td>
                  <td className="py-2 pr-4">{s.source_type}</td>
                  <td className="py-2 pr-4">{s.enabled ? 'Yes' : 'No'}</td>
                  <td className="py-2 pr-4">
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${complianceColor(s.compliance_status)}`}>
                      {s.compliance_status}
                    </span>
                  </td>
                  <td className="py-2 pr-4 tabular-nums">
                    {s.rate_limit_per_minute === null ? '—' : `${s.rate_limit_per_minute}/min`}
                  </td>
                  <td className="py-2">
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${sourceHealthColor(s.health)}`}>
                      {s.health}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
