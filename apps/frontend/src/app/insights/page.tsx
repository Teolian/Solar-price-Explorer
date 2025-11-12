'use client'

import { useState } from 'react'
import { api, type HourlyPatternsResponse } from '@/lib/api'
import { useI18n } from '@/lib/i18n'
import ReactEChartsCore from 'echarts-for-react/lib/core'
import * as echarts from 'echarts/core'
import { BarChart, LineChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  TitleComponent,
  LegendComponent,
  DataZoomComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  BarChart,
  LineChart,
  GridComponent,
  TooltipComponent,
  TitleComponent,
  LegendComponent,
  DataZoomComponent,
  CanvasRenderer,
])

const AREAS = [
  'HOKKAIDO', 'TOHOKU', 'TOKYO', 'CHUBU', 'HOKURIKU',
  'KANSAI', 'CHUGOKU', 'SHIKOKU', 'KYUSHU'
]

const PERIODS = [
  { value: '7', label: 'Last 7 Days' },
  { value: '14', label: 'Last 14 Days' },
  { value: '30', label: 'Last 30 Days' },
  { value: '60', label: 'Last 60 Days' },
  { value: '90', label: 'Last 90 Days' },
]

export default function InsightsPage() {
  const { t } = useI18n()
  const [selectedArea, setSelectedArea] = useState('TOKYO')
  const [selectedPeriod, setSelectedPeriod] = useState('30')
  const [hourlyData, setHourlyData] = useState<HourlyPatternsResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchHourlyPatterns = async () => {
    setLoading(true)
    setError(null)

    try {
      // Calculate date range
      const endDate = new Date()
      const startDate = new Date()
      startDate.setDate(startDate.getDate() - parseInt(selectedPeriod))

      const result = await api.getHourlyPatterns(
        selectedArea,
        startDate.toISOString(),
        endDate.toISOString()
      )
      setHourlyData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch hourly patterns')
    } finally {
      setLoading(false)
    }
  }

  // Prepare chart data
  const getChartOption = () => {
    if (!hourlyData) return {}

    const hours = hourlyData.patterns.map(p => `${p.hour}:00`)
    const prices = hourlyData.patterns.map(p => p.avg_price)
    const ghiValues = hourlyData.patterns.map(p => p.avg_ghi)

    return {
      title: {
        text: `${selectedArea}: ${t('insights.chart_title')}`,
        subtext: `Average over ${selectedPeriod} days`,
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross',
          crossStyle: {
            color: '#999'
          }
        },
        formatter: (params: any) => {
          const hour = params[0].axisValue
          let tooltip = `<strong>${hour}</strong><br/>`
          params.forEach((param: any) => {
            if (param.seriesName === 'Price') {
              tooltip += `${param.marker} ${param.seriesName}: ${param.value.toFixed(2)} JPY/kWh<br/>`
            } else {
              tooltip += `${param.marker} ${param.seriesName}: ${param.value.toFixed(1)} W/m²<br/>`
            }
          })
          return tooltip
        }
      },
      legend: {
        data: [t('overview.price'), t('overview.radiation')],
        top: 40,
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        top: '20%',
        containLabel: true
      },
      xAxis: [
        {
          type: 'category',
          data: hours,
          axisPointer: {
            type: 'shadow'
          },
          name: t('chart.hour_of_day'),
          nameLocation: 'middle',
          nameGap: 35,
        }
      ],
      yAxis: [
        {
          type: 'value',
          name: t('chart.price_jpy_kwh'),
          position: 'left',
          axisLabel: {
            formatter: '{value}'
          }
        },
        {
          type: 'value',
          name: t('chart.solar_radiation'),
          position: 'right',
          axisLabel: {
            formatter: '{value}'
          }
        }
      ],
      dataZoom: [
        {
          type: 'inside',
          start: 0,
          end: 100,
          xAxisIndex: 0,
        },
        {
          type: 'slider',
          start: 0,
          end: 100,
          xAxisIndex: 0,
          bottom: '5%',
        }
      ],
      series: [
        {
          name: t('overview.price'),
          type: 'bar',
          data: prices,
          itemStyle: {
            color: '#3b82f6',
          },
          yAxisIndex: 0,
        },
        {
          name: t('overview.radiation'),
          type: 'line',
          smooth: true,
          data: ghiValues,
          itemStyle: {
            color: '#f59e0b',
          },
          lineStyle: {
            width: 3,
          },
          yAxisIndex: 1,
        }
      ]
    }
  }

  // Calculate key insights
  const getInsights = () => {
    if (!hourlyData || hourlyData.patterns.length === 0) return null

    // Find peak solar hour and corresponding price
    const peakSolarHour = hourlyData.patterns.reduce((max, p) =>
      p.avg_ghi > max.avg_ghi ? p : max
    )

    // Find midnight hour (lowest solar) and corresponding price
    const midnightHour = hourlyData.patterns.find(p => p.hour === 0) || hourlyData.patterns[0]

    // Find highest and lowest price hours
    const highestPriceHour = hourlyData.patterns.reduce((max, p) =>
      p.avg_price > max.avg_price ? p : max
    )
    const lowestPriceHour = hourlyData.patterns.reduce((min, p) =>
      p.avg_price < min.avg_price ? p : min
    )

    // Calculate daytime (6-18) vs nighttime (0-6, 18-24) average prices
    const daytimePatterns = hourlyData.patterns.filter(p => p.hour >= 6 && p.hour < 18)
    const nighttimePatterns = hourlyData.patterns.filter(p => p.hour < 6 || p.hour >= 18)

    const avgDaytimePrice = daytimePatterns.reduce((sum, p) => sum + p.avg_price, 0) / daytimePatterns.length
    const avgNighttimePrice = nighttimePatterns.reduce((sum, p) => sum + p.avg_price, 0) / nighttimePatterns.length

    return {
      peakSolarHour,
      midnightHour,
      highestPriceHour,
      lowestPriceHour,
      avgDaytimePrice,
      avgNighttimePrice,
      priceDifference: avgNighttimePrice - avgDaytimePrice,
      percentDifference: ((avgNighttimePrice - avgDaytimePrice) / avgDaytimePrice) * 100,
    }
  }

  const insights = hourlyData ? getInsights() : null

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Hourly Patterns</h1>
        <p className="text-muted-foreground">
          Discover how solar radiation affects electricity prices throughout the day
        </p>
      </div>

      {/* Controls */}
      <div className="rounded-lg border bg-card p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium mb-2">Area</label>
            <select
              className="w-full p-2 border rounded-md"
              value={selectedArea}
              onChange={(e) => setSelectedArea(e.target.value)}
            >
              {AREAS.map((area) => (
                <option key={area} value={area}>
                  {area}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Time Period</label>
            <select
              className="w-full p-2 border rounded-md"
              value={selectedPeriod}
              onChange={(e) => setSelectedPeriod(e.target.value)}
            >
              {PERIODS.map((period) => (
                <option key={period.value} value={period.value}>
                  {period.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <button
          className="w-full md:w-auto px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
          onClick={fetchHourlyPatterns}
          disabled={loading}
        >
          {loading ? 'Loading...' : 'Analyze Patterns'}
        </button>
      </div>

      {error && (
        <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}

      {/* Chart */}
      {hourlyData && (
        <div className="rounded-lg border bg-card p-6">
          <ReactEChartsCore
            echarts={echarts}
            option={getChartOption()}
            style={{ height: '500px' }}
            notMerge={true}
            lazyUpdate={true}
          />
          <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-950 rounded-lg text-sm">
            <p className="font-medium mb-2 uppercase text-xs tracking-wide text-blue-700 dark:text-blue-300">Chart Guide</p>
            <ul className="space-y-1">
              <li>• <span className="font-medium text-blue-600">Blue bars</span> = Average electricity price by hour</li>
              <li>• <span className="font-medium text-amber-600">Orange line</span> = Average solar radiation by hour</li>
              <li>• Notice how prices tend to <strong>drop</strong> when solar radiation <strong>increases</strong> (inverse relationship)</li>
              <li>• This pattern reveals solar generation's impact on market prices</li>
            </ul>
          </div>
        </div>
      )}

      {/* Key Insights Cards */}
      {insights && (
        <div className="space-y-6">
          <h2 className="text-2xl font-semibold">Key Insights</h2>

          {/* Price Comparison */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="rounded-lg border bg-card p-6">
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Daytime Average</h3>
              <div className="text-3xl font-bold text-green-600">
                {insights.avgDaytimePrice.toFixed(2)}
              </div>
              <div className="text-sm text-muted-foreground">JPY/kWh (6am-6pm)</div>
              <p className="text-xs mt-2 text-muted-foreground">
                When solar generation is active
              </p>
            </div>

            <div className="rounded-lg border bg-card p-6">
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Nighttime Average</h3>
              <div className="text-3xl font-bold text-red-600">
                {insights.avgNighttimePrice.toFixed(2)}
              </div>
              <div className="text-sm text-muted-foreground">JPY/kWh (6pm-6am)</div>
              <p className="text-xs mt-2 text-muted-foreground">
                When solar generation is inactive
              </p>
            </div>

            <div className="rounded-lg border bg-card p-6">
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Price Difference</h3>
              <div className="text-3xl font-bold">
                {insights.priceDifference > 0 ? '+' : ''}
                {insights.priceDifference.toFixed(2)}
              </div>
              <div className="text-sm text-muted-foreground">
                {insights.percentDifference > 0 ? '+' : ''}
                {insights.percentDifference.toFixed(1)}%
              </div>
              <p className="text-xs mt-2 text-muted-foreground">
                Night vs Day price premium
              </p>
            </div>
          </div>

          {/* Peak Hours Analysis */}
          <div className="rounded-lg border bg-card p-6">
            <h3 className="text-lg font-semibold mb-4">Peak Hours Analysis</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="p-4 bg-amber-50 dark:bg-amber-950 rounded-lg">
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="font-medium uppercase text-xs tracking-wide text-amber-700 dark:text-amber-300">Peak Solar Hour</h4>
                    <span className="text-2xl font-bold text-amber-600">
                      {insights.peakSolarHour.hour}:00
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <div className="text-muted-foreground">Solar Radiation</div>
                      <div className="font-semibold">{insights.peakSolarHour.avg_ghi.toFixed(1)} W/m²</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Price</div>
                      <div className="font-semibold">{insights.peakSolarHour.avg_price.toFixed(2)} JPY/kWh</div>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-green-50 dark:bg-green-950 rounded-lg">
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="font-medium uppercase text-xs tracking-wide text-green-700 dark:text-green-300">Lowest Price Hour</h4>
                    <span className="text-2xl font-bold text-green-600">
                      {insights.lowestPriceHour.hour}:00
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <div className="text-muted-foreground">Price</div>
                      <div className="font-semibold">{insights.lowestPriceHour.avg_price.toFixed(2)} JPY/kWh</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Solar Radiation</div>
                      <div className="font-semibold">{insights.lowestPriceHour.avg_ghi.toFixed(1)} W/m²</div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div className="p-4 bg-slate-50 dark:bg-slate-950 rounded-lg">
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="font-medium uppercase text-xs tracking-wide text-slate-700 dark:text-slate-300">Midnight Hour</h4>
                    <span className="text-2xl font-bold text-slate-600">
                      {insights.midnightHour.hour}:00
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <div className="text-muted-foreground">Solar Radiation</div>
                      <div className="font-semibold">{insights.midnightHour.avg_ghi.toFixed(1)} W/m²</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Price</div>
                      <div className="font-semibold">{insights.midnightHour.avg_price.toFixed(2)} JPY/kWh</div>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-red-50 dark:bg-red-950 rounded-lg">
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="font-medium uppercase text-xs tracking-wide text-red-700 dark:text-red-300">Highest Price Hour</h4>
                    <span className="text-2xl font-bold text-red-600">
                      {insights.highestPriceHour.hour}:00
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <div className="text-muted-foreground">Price</div>
                      <div className="font-semibold">{insights.highestPriceHour.avg_price.toFixed(2)} JPY/kWh</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Solar Radiation</div>
                      <div className="font-semibold">{insights.highestPriceHour.avg_ghi.toFixed(1)} W/m²</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Detailed Pattern Table */}
          <div className="rounded-lg border bg-card p-6">
            <h3 className="text-lg font-semibold mb-4">Hourly Details</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">Hour</th>
                    <th className="text-right p-2">Avg Price (JPY/kWh)</th>
                    <th className="text-right p-2">Avg Solar (W/m²)</th>
                    <th className="text-right p-2">Sample Size</th>
                  </tr>
                </thead>
                <tbody>
                  {hourlyData.patterns.map((pattern) => (
                    <tr key={pattern.hour} className="border-b hover:bg-accent">
                      <td className="p-2 font-medium">{pattern.hour}:00</td>
                      <td className="text-right p-2">{pattern.avg_price.toFixed(2)}</td>
                      <td className="text-right p-2">{pattern.avg_ghi.toFixed(1)}</td>
                      <td className="text-right p-2 text-muted-foreground">
                        {pattern.count.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Interpretation Guide */}
          <div className="rounded-lg border bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950 dark:to-indigo-950 p-6">
            <h3 className="text-lg font-semibold mb-3 uppercase text-sm tracking-wide">Understanding the Pattern</h3>
            <div className="space-y-2 text-sm">
              <p>
                <strong>The Solar Effect:</strong> This analysis reveals how solar power generation influences
                electricity spot prices throughout the day in {selectedArea}.
              </p>
              <p>
                <strong>Key Pattern:</strong> During peak solar hours (typically 11am-2pm), increased solar
                generation reduces reliance on conventional power plants, which typically lowers spot prices.
                At night, when solar is unavailable, prices often rise.
              </p>
              <p>
                <strong>Market Dynamics:</strong> The price difference between day and night
                ({insights.percentDifference.toFixed(1)}%) represents the economic value of solar
                generation in reducing peak demand and displacing more expensive conventional power sources.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
