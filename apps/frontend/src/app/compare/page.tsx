'use client'

import { useState } from 'react'
import { api, type MultiAreaComparisonResponse } from '@/lib/api'
import { useI18n } from '@/lib/i18n'
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
  const { t } = useI18n()
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
        text: t('compare.price_comparison'),
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
        data: [t('compare.average'), t('compare.minimum'), t('compare.maximum')],
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
        name: t('chart.price_jpy_kwh'),
      },
      series: [
        {
          name: t('compare.average'),
          type: 'bar',
          data: avgPrices,
          itemStyle: {
            color: '#3b82f6',
          },
        },
        {
          name: t('compare.minimum'),
          type: 'bar',
          data: minPrices,
          itemStyle: {
            color: '#10b981',
          },
        },
        {
          name: t('compare.maximum'),
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
        text: t('compare.solar_comparison'),
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
        name: t('chart.solar_radiation'),
      },
      series: [
        {
          name: t('compare.avg_ghi'),
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
        text: t('compare.correlation_chart'),
        left: 'center',
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        },
        formatter: (params: any) => {
          const value = params[0].value
          const strength = Math.abs(value) > 0.5 ? t('correlations.strong') : Math.abs(value) > 0.3 ? t('correlations.moderate') : t('correlations.weak')
          return `<strong>${params[0].axisValue}</strong><br/>${params[0].marker} ${t('overview.correlation')}: ${value.toFixed(3)}<br/>${t('correlations.strength')}: ${strength}`
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
        name: t('correlations.coefficient'),
        min: -1,
        max: 1,
      },
      series: [
        {
          name: t('overview.correlation'),
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
        <h1 className="text-3xl font-bold">{t('compare.title')}</h1>
        <p className="text-muted-foreground">
          {t('compare.subtitle')}
        </p>
      </div>

      {/* Area Selection */}
      <div className="rounded-lg border bg-card p-6">
        <h2 className="text-lg font-semibold mb-4">{t('compare.select_areas')}</h2>
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
            <label className="block text-sm font-medium mb-2">{t('compare.time_period')}</label>
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
              {loading ? t('common.loading') : `${t('compare.compare_button')} ${selectedAreas.length} ${selectedAreas.length !== 1 ? t('compare.areas') : t('common.area')}`}
            </button>
          </div>
        </div>

        {selectedAreas.length === 0 && (
          <p className="text-sm text-amber-600">{t('compare.select_at_least_one')}</p>
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
            <h3 className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wide">{t('compare.lowest_price')}</h3>
            <div className="text-2xl font-bold text-green-600">{insights.lowestPrice.area}</div>
            <div className="text-lg">{insights.lowestPrice.avg_price.toFixed(2)} JPY/kWh</div>
          </div>

          <div className="rounded-lg border bg-card p-6">
            <h3 className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wide">{t('compare.highest_price')}</h3>
            <div className="text-2xl font-bold text-red-600">{insights.highestPrice.area}</div>
            <div className="text-lg">{insights.highestPrice.avg_price.toFixed(2)} JPY/kWh</div>
          </div>

          <div className="rounded-lg border bg-card p-6">
            <h3 className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wide">{t('compare.highest_solar')}</h3>
            <div className="text-2xl font-bold text-amber-600">{insights.highestSolar.area}</div>
            <div className="text-lg">{insights.highestSolar.avg_ghi.toFixed(1)} W/m²</div>
          </div>

          {insights.strongestCorr && (
            <div className="rounded-lg border bg-card p-6">
              <h3 className="text-xs font-medium text-muted-foreground mb-2 uppercase tracking-wide">{t('compare.strongest_correlation')}</h3>
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
              {t('compare.price_chart_desc')}
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
              {t('compare.solar_chart_desc')}
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
              {t('compare.correlation_chart_desc')}
            </p>
          </div>

          {/* Detailed Table */}
          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-xl font-semibold mb-4">{t('compare.detailed_stats')}</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">{t('common.area')}</th>
                    <th className="text-right p-2">{t('compare.avg_price')}</th>
                    <th className="text-right p-2">{t('compare.min_price')}</th>
                    <th className="text-right p-2">{t('compare.max_price')}</th>
                    <th className="text-right p-2">{t('compare.avg_solar')}</th>
                    <th className="text-right p-2">{t('overview.correlation')}</th>
                    <th className="text-right p-2">{t('compare.data_points')}</th>
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
            <h3 className="text-lg font-semibold mb-3 uppercase text-sm tracking-wide">Regional Patterns</h3>
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
