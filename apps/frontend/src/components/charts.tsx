'use client'

import React from 'react'
import ReactEChartsCore from 'echarts-for-react/lib/core'
import * as echarts from 'echarts/core'
import { LineChart, ScatterChart as EChartsScatter } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  TitleComponent,
  LegendComponent,
  DataZoomComponent,
  MarkLineComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  LineChart,
  EChartsScatter,
  GridComponent,
  TooltipComponent,
  TitleComponent,
  LegendComponent,
  DataZoomComponent,
  MarkLineComponent,
  CanvasRenderer,
])

interface DataPoint {
  timestamp: string
  value: number
}

interface TimeSeriesChartProps {
  title: string
  data: DataPoint[]
  yAxisLabel?: string
  height?: number
}

export function TimeSeriesChart({
  title,
  data,
  yAxisLabel = 'Value',
  height = 400,
}: TimeSeriesChartProps) {
  const option = {
    title: {
      text: title,
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
      },
    },
    xAxis: {
      type: 'time',
      boundaryGap: false,
    },
    yAxis: {
      type: 'value',
      name: yAxisLabel,
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100,
      },
      {
        start: 0,
        end: 100,
      },
    ],
    series: [
      {
        name: yAxisLabel,
        type: 'line',
        smooth: true,
        data: data.map((d) => [d.timestamp, d.value]),
      },
    ],
  }

  return (
    <ReactEChartsCore
      echarts={echarts}
      option={option}
      style={{ height: `${height}px` }}
      notMerge={true}
      lazyUpdate={true}
    />
  )
}

interface MultiSeriesData {
  name: string
  data: DataPoint[]
  color?: string
}

interface MultiSeriesChartProps {
  title: string
  series: MultiSeriesData[]
  yAxisLabel?: string
  height?: number
}

export function MultiSeriesChart({
  title,
  series,
  yAxisLabel = 'Value',
  height = 400,
}: MultiSeriesChartProps) {
  const option = {
    title: {
      text: title,
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
      },
    },
    legend: {
      data: series.map((s) => s.name),
      top: 30,
    },
    xAxis: {
      type: 'time',
      boundaryGap: false,
    },
    yAxis: {
      type: 'value',
      name: yAxisLabel,
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100,
      },
      {
        start: 0,
        end: 100,
      },
    ],
    series: series.map((s) => ({
      name: s.name,
      type: 'line',
      smooth: true,
      data: s.data.map((d) => [d.timestamp, d.value]),
      itemStyle: s.color ? { color: s.color } : undefined,
    })),
  }

  return (
    <ReactEChartsCore
      echarts={echarts}
      option={option}
      style={{ height: `${height}px` }}
      notMerge={true}
      lazyUpdate={true}
    />
  )
}

interface ScatterData {
  x: number
  y: number
  label?: string
}

interface ScatterChartProps {
  title: string
  data: ScatterData[]
  xAxisLabel?: string
  yAxisLabel?: string
  height?: number
  showTrendLine?: boolean
  correlation?: number
}

/**
 * Calculate linear regression for trend line
 */
function calculateLinearRegression(data: ScatterData[]): { slope: number; intercept: number } {
  const n = data.length
  const sumX = data.reduce((sum, d) => sum + d.x, 0)
  const sumY = data.reduce((sum, d) => sum + d.y, 0)
  const sumXY = data.reduce((sum, d) => sum + d.x * d.y, 0)
  const sumX2 = data.reduce((sum, d) => sum + d.x * d.x, 0)

  const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX)
  const intercept = (sumY - slope * sumX) / n

  return { slope, intercept }
}

export function ScatterChart({
  title,
  data,
  xAxisLabel = 'X',
  yAxisLabel = 'Y',
  height = 400,
  showTrendLine = false,
  correlation,
}: ScatterChartProps) {
  // Calculate trend line if requested
  let trendLineData: number[][] = []
  if (showTrendLine && data.length > 1) {
    const { slope, intercept } = calculateLinearRegression(data)
    const xMin = Math.min(...data.map((d) => d.x))
    const xMax = Math.max(...data.map((d) => d.x))
    trendLineData = [
      [xMin, slope * xMin + intercept],
      [xMax, slope * xMax + intercept],
    ]
  }

  // Build subtitle with correlation if provided
  const subtitle = correlation !== undefined
    ? `Correlation: ${correlation.toFixed(3)}`
    : undefined

  const option = {
    title: {
      text: title,
      subtext: subtitle,
      left: 'center',
    },
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        if (params.seriesType === 'scatter') {
          return `${xAxisLabel}: ${params.value[0].toFixed(2)}<br/>${yAxisLabel}: ${params.value[1].toFixed(2)}`
        }
        return params.seriesName
      },
    },
    grid: {
      left: '10%',
      right: '5%',
      bottom: '15%',
      top: subtitle ? '20%' : '15%',
    },
    xAxis: {
      type: 'value',
      name: xAxisLabel,
      nameLocation: 'middle',
      nameGap: 30,
    },
    yAxis: {
      type: 'value',
      name: yAxisLabel,
      nameLocation: 'middle',
      nameGap: 50,
    },
    series: [
      {
        name: 'Data Points',
        type: 'scatter',
        data: data.map((d) => [d.x, d.y]),
        symbolSize: 6,
        itemStyle: {
          color: 'rgba(59, 130, 246, 0.6)',
          borderColor: 'rgb(59, 130, 246)',
          borderWidth: 1,
        },
        emphasis: {
          itemStyle: {
            color: 'rgb(59, 130, 246)',
            borderColor: 'rgb(29, 78, 216)',
            borderWidth: 2,
          },
        },
      },
      ...(showTrendLine && trendLineData.length > 0
        ? [
            {
              name: 'Trend Line',
              type: 'line',
              data: trendLineData,
              lineStyle: {
                color: 'rgba(239, 68, 68, 0.8)',
                width: 2,
                type: 'dashed' as const,
              },
              symbol: 'none',
              tooltip: {
                show: false,
              },
            },
          ]
        : []),
    ],
  }

  return (
    <ReactEChartsCore
      echarts={echarts}
      option={option}
      style={{ height: `${height}px` }}
      notMerge={true}
      lazyUpdate={true}
    />
  )
}
