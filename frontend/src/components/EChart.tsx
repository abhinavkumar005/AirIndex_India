/**
 * Thin React wrapper around ECharts instances.
 *
 * Renders into a div and manages init/resize/dispose lifecycle.
 * `option` changes re-apply via setOption (notReplace by default so
 * incremental data updates keep animations).
 */

import { useEffect, useRef } from 'react'
import * as echarts from 'echarts'

interface EChartProps {
  option: echarts.EChartsOption
  height?: number
  className?: string
}

export default function EChart({ option, height = 360, className = '' }: EChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<echarts.ECharts | null>(null)

  useEffect(() => {
    if (!containerRef.current) return

    const chart = echarts.init(containerRef.current)
    chartRef.current = chart

    const handleResize = () => chart.resize()
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      chart.dispose()
      chartRef.current = null
    }
  }, [])

  useEffect(() => {
    if (chartRef.current) {
      chartRef.current.setOption(option)
    }
  }, [option])

  return (
    <div
      ref={containerRef}
      className={className}
      style={{ width: '100%', height }}
    />
  )
}
