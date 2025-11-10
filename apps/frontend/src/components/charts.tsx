'use client'

import React from 'react'
import ReactEChartsCore from 'echarts-for-react/lib/core'
import * as echarts from 'echarts/core'
import { LineChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  TitleComponent,
  LegendComponent,
  DataZoomComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  LineChart,
  GridComponent,
  TooltipComponent,
  TitleComponent,
  LegendComponent,
  DataZoomComponent,
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
}

export function ScatterChart({
  title,
  data,
  xAxisLabel = 'X',
  yAxisLabel = 'Y',
  height = 400,
}: ScatterChartProps) {
  const option = {
    title: {
      text: title,
      left: 'center',
    },
    tooltip: {
      trigger: 'item',
    },
    xAxis: {
      type: 'value',
      name: xAxisLabel,
    },
    yAxis: {
      type: 'value',
      name: yAxisLabel,
    },
    series: [
      {
        type: 'scatter',
        data: data.map((d) => [d.x, d.y]),
        symbolSize: 8,
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
