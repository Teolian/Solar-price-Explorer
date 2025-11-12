'use client'

import { useState } from 'react'
import { api, type MultiAreaComparisonResponse } from '@/lib/api'
import ReactEChartsCore from 'echarts-for-react/lib/core'
import * as echarts from 'echarts/core'
import { BarChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  TitleComponent,
  LegendComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  BarChart,
  GridComponent,
  TooltipComponent,
  TitleComponent,
  LegendComponent,
  CanvasRenderer,
])

const ALL_AREAS = [
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

export default function ComparePage() {
  const [selectedAreas, setSelectedAreas] = useState<string[]>(['TOKYO', 'KANSAI', 'HOKKAIDO'])
  const [selectedPeriod, setSelectedPeriod] = useState('30')
  const [comparisonData, setComparisonData] = useState<MultiAreaComparisonResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const toggleArea = (area: string) => {
    if (selectedAreas.includes(area)) {
      setSelectedAreas(selectedAreas.filter(a => a !== area))
    } else {
      setSelectedAreas([...selectedAreas, area])
    }
  }

  const fetchComparison = async () => {
    if (selectedAreas.length === 0) {
      setError('Please select at least one area')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const endDate = new Date()
      const startDate = new Date()
      startDate.setDate(startDate.getDate() - parseInt(selectedPeriod))

      const result = await api.getMultiAreaComparison(
        selectedAreas,
        startDate.toISOString(),
        endDate.toISOString()
      )
      setComparisonData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch comparison data')
    } finally {
      setLoading(false)
    }
  }

  // Prepare chart for average prices
  const getPriceComparisonChart = () => {
    if (!comparisonData) return {}

    const areas = comparisonData.areas.map(a => a.area)
    const avgPrices = comparisonData.areas.map(a => a.avg_price)
    const minPrices = comparisonData.areas.map(a => a.min_price)
    const maxPrices = comparisonData.areas.map(a => a.max_price)

    return {
      title: {
        text: 'Price Comparison Across Areas',
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        },
        formatter: (params: any) => {
          let tooltip = `<strong>${params[0].axisValue}</strong><br/>`
          params.forEach((param: any) => {
            tooltip += `${param.marker} ${param.seriesName}: ${param.value.toFixed(2)} JPY/kWh<br/>`
          })
          return tooltip
        }
      },
      legend: {
        data: ['Average', 'Minimum', 'Maximum'],
        top: 35,
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '10%',
        top: '20%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: areas,
        axisLabel: {
          rotate: 45,
        }
      },
      yAxis: {
        type: 'value',
        name: 'Price (JPY/kWh)',
      },
      series: [
        {
          name: 'Average',
          type: 'bar',
          data: avgPrices,
          itemStyle: {
            color: '#3b82f6',
          },
        },
        {
          name: 'Minimum',
          type: 'bar',
          data: minPrices,
          itemStyle: {
            color: '#10b981',
          },
        },
        {
          name: 'Maximum',
          type: 'bar',
          data: maxPrices,
          itemStyle: {
            color: '#ef4444',
          },
        }
      ]
    }
  }

  // Prepare chart for solar radiation
  const getSolarComparisonChart = () => {
    if (!comparisonData) return {}

    const areas = comparisonData.areas.map(a => a.area)
    const avgGhi = comparisonData.areas.map(a => a.avg_ghi)

    return {
      title: {
        text: 'Average Solar Radiation (GHI) Across Areas',
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        },
        formatter: (params: any) => {
          return `<strong>${params[0].axisValue}</strong><br/>${params[0].marker} ${params[0].seriesName}: ${params[0].value.toFixed(1)} W/m²`
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '10%',
        top: '15%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: areas,
        axisLabel: {
          rotate: 45,
        }
      },
      yAxis: {
        type: 'value',
        name: 'Radiation (W/m²)',
      },
      series: [
        {
          name: 'Avg GHI',
          type: 'bar',
          data: avgGhi,
          itemStyle: {
            color: '#f59e0b',
          },
        }
      ]
    }
  }

  // Prepare chart for correlations
  const getCorrelationChart = () => {
    if (!comparisonData) return {}

    const areasWithCorr = comparisonData.areas.filter(a => a.correlation !== null && a.correlation !== undefined)
    const areas = areasWithCorr.map(a => a.area)
    const correlations = areasWithCorr.map(a => a.correlation!)

    return {
      title: {
        text: 'Price-Solar Correlation by Area',
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        },
        formatter: (params: any) => {
          const value = params[0].value
          const strength = Math.abs(value) > 0.5 ? 'Strong' : Math.abs(value) > 0.3 ? 'Moderate' : 'Weak'
          return `<strong>${params[0].axisValue}</strong><br/>${params[0].marker} Correlation: ${value.toFixed(3)}<br/>Strength: ${strength}`
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '10%',
        top: '15%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: areas,
        axisLabel: {
          rotate: 45,
        }
      },
      yAxis: {
        type: 'value',
        name: 'Correlation Coefficient',
        min: -1,
        max: 1,
      },
      series: [
        {
          name: 'Correlation',
          type: 'bar',
          data: correlations,
          itemStyle: {
            color: (params: any) => {
              const value = params.value
              if (Math.abs(value) > 0.5) return '#10b981' // Green for strong
              if (Math.abs(value) > 0.3) return '#f59e0b' // Amber for moderate
              return '#94a3b8' // Gray for weak
            }
          },
        }
      ]
    }
  }

  // Find areas with highest/lowest values
  const getInsights = () => {
    if (!comparisonData || comparisonData.areas.length === 0) return null

    const highestPrice = comparisonData.areas.reduce((max, a) =>
      a.avg_price > max.avg_price ? a : max
    )
    const lowestPrice = comparisonData.areas.reduce((min, a) =>
      a.avg_price < min.avg_price ? a : min
    )
    const highestSolar = comparisonData.areas.reduce((max, a) =>
      a.avg_ghi > max.avg_ghi ? a : max
    )
    const strongestCorr = comparisonData.areas
      .filter(a => a.correlation !== null)
      .reduce((max, a) =>
        Math.abs(a.correlation!) > Math.abs(max.correlation!) ? a : max,
        comparisonData.areas.find(a => a.correlation !== null) || comparisonData.areas[0]
      )

    return {
      highestPrice,
      lowestPrice,
      highestSolar,
      strongestCorr: strongestCorr.correlation !== null ? strongestCorr : null,
    }
  }

  const insights = comparisonData ? getInsights() : null

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Multi-Area Comparison</h1>
        <p className="text-muted-foreground">
          Compare electricity prices and solar radiation across Japanese power areas
        </p>
      </div>

      {/* Area Selection */}
      <div className="rounded-lg border bg-card p-6">
        <h2 className="text-lg font-semibold mb-4">Select Areas to Compare</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3 mb-4">
          {ALL_AREAS.map((area) => (
            <label
              key={area}
              className={`flex items-center p-3 border rounded-md cursor-pointer transition-colors ${
                selectedAreas.includes(area)
                  ? 'bg-primary text-primary-foreground border-primary'
                  : 'hover:bg-accent'
              }`}
            >
              <input
                type="checkbox"
                checked={selectedAreas.includes(area)}
                onChange={() => toggleArea(area)}
                className="mr-2"
              />
              <span className="text-sm font-medium">{area}</span>
            </label>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
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

          <div className="flex items-end">
            <button
              className="w-full px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
              onClick={fetchComparison}
              disabled={loading || selectedAreas.length === 0}
            >
              {loading ? 'Loading...' : `Compare ${selectedAreas.length} Area${selectedAreas.length !== 1 ? 's' : ''}`}
            </button>
          </div>
        </div>

        {selectedAreas.length === 0 && (
          <p className="text-sm text-amber-600">Please select at least one area</p>
        )}
      </div>

      {error && (
        <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}

      {/* Key Insights */}
      {insights && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="rounded-lg border bg-card p-6">
            <h3 className="text-sm font-medium text-muted-foreground mb-2">💰 Lowest Avg Price</h3>
            <div className="text-2xl font-bold text-green-600">{insights.lowestPrice.area}</div>
            <div className="text-lg">{insights.lowestPrice.avg_price.toFixed(2)} JPY/kWh</div>
          </div>

          <div className="rounded-lg border bg-card p-6">
            <h3 className="text-sm font-medium text-muted-foreground mb-2">📈 Highest Avg Price</h3>
            <div className="text-2xl font-bold text-red-600">{insights.highestPrice.area}</div>
            <div className="text-lg">{insights.highestPrice.avg_price.toFixed(2)} JPY/kWh</div>
          </div>

          <div className="rounded-lg border bg-card p-6">
            <h3 className="text-sm font-medium text-muted-foreground mb-2">☀️ Highest Solar</h3>
            <div className="text-2xl font-bold text-amber-600">{insights.highestSolar.area}</div>
            <div className="text-lg">{insights.highestSolar.avg_ghi.toFixed(1)} W/m²</div>
          </div>

          {insights.strongestCorr && (
            <div className="rounded-lg border bg-card p-6">
              <h3 className="text-sm font-medium text-muted-foreground mb-2">🔗 Strongest Correlation</h3>
              <div className="text-2xl font-bold text-blue-600">{insights.strongestCorr.area}</div>
              <div className="text-lg">{insights.strongestCorr.correlation?.toFixed(3)}</div>
            </div>
          )}
        </div>
      )}

      {/* Charts */}
      {comparisonData && (
        <div className="space-y-6">
          {/* Price Comparison Chart */}
          <div className="rounded-lg border bg-card p-6">
            <ReactEChartsCore
              echarts={echarts}
              option={getPriceComparisonChart()}
              style={{ height: '400px' }}
              notMerge={true}
              lazyUpdate={true}
            />
            <p className="text-sm text-muted-foreground mt-4 text-center">
              Compare average, minimum, and maximum electricity prices across selected areas
            </p>
          </div>

          {/* Solar Comparison Chart */}
          <div className="rounded-lg border bg-card p-6">
            <ReactEChartsCore
              echarts={echarts}
              option={getSolarComparisonChart()}
              style={{ height: '350px' }}
              notMerge={true}
              lazyUpdate={true}
            />
            <p className="text-sm text-muted-foreground mt-4 text-center">
              Average solar radiation (GHI) shows geographical and weather pattern differences
            </p>
          </div>

          {/* Correlation Comparison Chart */}
          <div className="rounded-lg border bg-card p-6">
            <ReactEChartsCore
              echarts={echarts}
              option={getCorrelationChart()}
              style={{ height: '350px' }}
              notMerge={true}
              lazyUpdate={true}
            />
            <p className="text-sm text-muted-foreground mt-4 text-center">
              Negative correlation indicates solar generation reduces prices; positive indicates opposite effect
            </p>
          </div>

          {/* Detailed Table */}
          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-xl font-semibold mb-4">Detailed Statistics</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">Area</th>
                    <th className="text-right p-2">Avg Price</th>
                    <th className="text-right p-2">Min Price</th>
                    <th className="text-right p-2">Max Price</th>
                    <th className="text-right p-2">Avg Solar</th>
                    <th className="text-right p-2">Correlation</th>
                    <th className="text-right p-2">Data Points</th>
                  </tr>
                </thead>
                <tbody>
                  {comparisonData.areas.map((area) => (
                    <tr key={area.area} className="border-b hover:bg-accent">
                      <td className="p-2 font-medium">{area.area}</td>
                      <td className="text-right p-2">{area.avg_price.toFixed(2)} JPY/kWh</td>
                      <td className="text-right p-2 text-green-600">{area.min_price.toFixed(2)}</td>
                      <td className="text-right p-2 text-red-600">{area.max_price.toFixed(2)}</td>
                      <td className="text-right p-2">{area.avg_ghi.toFixed(1)} W/m²</td>
                      <td className="text-right p-2">
                        {area.correlation !== null && area.correlation !== undefined ? (
                          <span className={
                            Math.abs(area.correlation) > 0.5 ? 'text-green-600 font-semibold' :
                            Math.abs(area.correlation) > 0.3 ? 'text-amber-600' :
                            'text-muted-foreground'
                          }>
                            {area.correlation.toFixed(3)}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">N/A</span>
                        )}
                      </td>
                      <td className="text-right p-2 text-muted-foreground">
                        {area.data_points.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Regional Insights */}
          <div className="rounded-lg border bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950 dark:to-indigo-950 p-6">
            <h3 className="text-lg font-semibold mb-3">📍 Regional Patterns</h3>
            <div className="space-y-2 text-sm">
              <p>
                <strong>Price Variation:</strong> Different areas show varying price levels due to generation mix,
                transmission constraints, and local demand patterns.
              </p>
              <p>
                <strong>Solar Impact:</strong> Areas with high solar penetration (like Tokyo, Kansai) typically
                show stronger negative correlations during daytime hours.
              </p>
              <p>
                <strong>Geographical Factors:</strong> Northern areas (Hokkaido) receive less solar radiation
                on average, while southern/western areas benefit from more consistent sunlight.
              </p>
              <p>
                <strong>Grid Dynamics:</strong> Isolated grids (Hokkaido) may show higher price volatility
                compared to interconnected areas in Honshu.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
