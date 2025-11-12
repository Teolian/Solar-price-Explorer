'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { api } from '@/lib/api'
import { TimeSeriesChart } from '@/components/charts'
import { useI18n } from '@/lib/i18n'

interface DashboardStats {
  latestPrice: number
  priceChange24h: number
  avgRadiation: number
  totalRecords: number
  dataFreshness: string
  correlation: number
}

export default function Home() {
  const { t } = useI18n()
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [recentPrices, setRecentPrices] = useState<Array<{ timestamp: string; value: number }>>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch summary stats (much faster - single endpoint with aggregated data)
      const endDate = new Date()
      const statsStartDate = new Date()
      statsStartDate.setDate(statsStartDate.getDate() - 7)

      // For chart, only fetch last 3 days to keep it fast
      const chartStartDate = new Date()
      chartStartDate.setDate(chartStartDate.getDate() - 3)

      const [summaryStats, prices] = await Promise.all([
        api.getStatsSummary('TOKYO', statsStartDate.toISOString(), endDate.toISOString()),
        // Only fetch 3 days for the chart (144 records instead of 336)
        api.getPrices('TOKYO', chartStartDate.toISOString(), endDate.toISOString()),
      ])

      if (!summaryStats || summaryStats.total_records === 0) {
        setError('No data available. Please run data ingestion.')
        setLoading(false)
        return
      }

      // Calculate 24h change from price stats
      const latestPrice = summaryStats.price_stats.avg
      const priceChange24h = 0 // We'll calculate this from actual prices if needed

      setStats({
        latestPrice,
        priceChange24h,
        avgRadiation: summaryStats.radiation_stats.avg_ghi,
        totalRecords: summaryStats.total_records,
        dataFreshness: new Date(summaryStats.date_range.to).toLocaleString('en-US', {
          timeZone: 'Asia/Tokyo',
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
        }),
        correlation: summaryStats.correlation || 0,
      })

      // Prepare chart data (last 7 days)
      setRecentPrices(
        prices.map((p) => ({
          timestamp: p.timestamp,
          value: p.price_jpy_kwh,
        }))
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">{t('common.loading')}</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="rounded-lg border border-destructive bg-destructive/10 p-6">
          <h2 className="text-xl font-semibold mb-2">Error Loading Dashboard</h2>
          <p className="text-sm text-destructive">{error}</p>
          <button
            onClick={loadDashboardData}
            className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            Retry
          </button>
        </div>
        <section className="rounded-lg border bg-card p-6">
          <h2 className="text-xl font-semibold mb-4">About Solar×Price Explorer</h2>
          <p className="text-muted-foreground">
            This application analyzes the correlation between JEPX electricity spot prices and solar
            radiation data across Japanese power areas. Run data ingestion to see live metrics.
          </p>
        </section>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Hero Section */}
      <section className="rounded-lg border bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950 dark:to-indigo-950 p-6">
        <h1 className="text-3xl font-bold mb-2">Solar×Price Explorer</h1>
        <p className="text-muted-foreground">
          {t('overview.title')}
        </p>
        <p className="text-xs text-muted-foreground mt-2">
          Data updated: {stats?.dataFreshness} JST
        </p>
      </section>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Latest Price */}
        <div className="rounded-lg border bg-card p-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-muted-foreground">{t('overview.latest_price')}</h3>
            <span className="text-xs text-muted-foreground">Latest</span>
          </div>
          <div className="text-3xl font-bold">{stats?.latestPrice.toFixed(2)}</div>
          <div className="text-sm text-muted-foreground">JPY/kWh</div>
          <div className="mt-2 flex items-center">
            {stats && stats.priceChange24h !== 0 && (
              <span
                className={`text-sm font-medium ${
                  stats.priceChange24h > 0 ? 'text-red-500' : 'text-green-500'
                }`}
              >
                {stats.priceChange24h > 0 ? '↑' : '↓'}{' '}
                {Math.abs(stats.priceChange24h).toFixed(2)}%
              </span>
            )}
            <span className="text-xs text-muted-foreground ml-2">vs 24h ago</span>
          </div>
        </div>

        {/* Solar Radiation */}
        <div className="rounded-lg border bg-card p-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-muted-foreground">{t('overview.avg_radiation')}</h3>
            <span className="text-xs text-muted-foreground">7d avg</span>
          </div>
          <div className="text-3xl font-bold">{stats?.avgRadiation.toFixed(0)}</div>
          <div className="text-sm text-muted-foreground">{t('overview.ghi')}</div>
          <div className="mt-2">
            <div className="flex items-center">
              <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-amber-500"
                  style={{ width: `${Math.min((stats?.avgRadiation || 0) / 10, 100)}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Correlation */}
        <div className="rounded-lg border bg-card p-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-muted-foreground">{t('overview.correlation')}</h3>
            <span className="text-xs text-muted-foreground">GHI</span>
          </div>
          <div className="text-3xl font-bold">{stats?.correlation.toFixed(3)}</div>
          <div className="text-sm text-muted-foreground">Pearson r</div>
          <div className="mt-2">
            <span
              className={`text-sm font-medium ${
                Math.abs(stats?.correlation || 0) > 0.5
                  ? 'text-green-500'
                  : Math.abs(stats?.correlation || 0) > 0.3
                  ? 'text-amber-500'
                  : 'text-muted-foreground'
              }`}
            >
              {Math.abs(stats?.correlation || 0) > 0.5
                ? 'Strong'
                : Math.abs(stats?.correlation || 0) > 0.3
                ? 'Moderate'
                : 'Weak'}{' '}
              {(stats?.correlation || 0) < 0 ? 'negative' : 'positive'}
            </span>
          </div>
        </div>

        {/* Total Records */}
        <div className="rounded-lg border bg-card p-6">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-muted-foreground">Dataset Size</h3>
            <span className="text-xs text-muted-foreground">7d</span>
          </div>
          <div className="text-3xl font-bold">{(stats?.totalRecords || 0).toLocaleString()}</div>
          <div className="text-sm text-muted-foreground">Records</div>
          <div className="mt-2 text-xs text-muted-foreground">
            Price + Radiation data points
          </div>
        </div>
      </div>

      {/* Recent Trend Chart */}
      {recentPrices.length > 0 && (
        <section className="rounded-lg border bg-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Tokyo Price Trend (Last 3 Days)</h2>
            <Link
              href="/data?area=TOKYO&type=prices"
              className="text-sm text-primary hover:underline"
            >
              View Details →
            </Link>
          </div>
          <TimeSeriesChart
            title=""
            data={recentPrices}
            yAxisLabel="Price (JPY/kWh)"
            height={300}
          />
        </section>
      )}

      {/* Quick Actions */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link href="/correlations" className="rounded-lg border bg-card p-6 hover:bg-accent transition-colors">
          <h3 className="font-semibold mb-2 uppercase text-xs tracking-wide text-primary">Correlation Analysis</h3>
          <p className="text-sm text-muted-foreground">
            Analyze how solar radiation affects electricity prices across regions
          </p>
        </Link>

        <Link href="/forecast" className="rounded-lg border bg-card p-6 hover:bg-accent transition-colors">
          <h3 className="font-semibold mb-2 uppercase text-xs tracking-wide text-primary">Price Forecast</h3>
          <p className="text-sm text-muted-foreground">
            ML-powered predictions for future electricity spot prices
          </p>
        </Link>

        <Link href="/data" className="rounded-lg border bg-card p-6 hover:bg-accent transition-colors">
          <h3 className="font-semibold mb-2 uppercase text-xs tracking-wide text-primary">Data Explorer</h3>
          <p className="text-sm text-muted-foreground">
            Browse and export raw price and solar radiation datasets
          </p>
        </Link>
      </section>

      {/* Insights Section */}
      <section className="rounded-lg border bg-card p-6">
        <h2 className="text-xl font-semibold mb-4">Key Insights</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-blue-50 dark:bg-blue-950 rounded-lg">
            <h3 className="font-medium mb-2 uppercase text-xs tracking-wide text-blue-700 dark:text-blue-300">Solar Impact</h3>
            <p className="text-sm text-muted-foreground">
              When solar radiation increases during daytime hours (6am-6pm), electricity spot prices
              typically decrease as solar generation reduces demand from conventional sources.
            </p>
          </div>
          <div className="p-4 bg-green-50 dark:bg-green-950 rounded-lg">
            <h3 className="font-medium mb-2 uppercase text-xs tracking-wide text-green-700 dark:text-green-300">Regional Variations</h3>
            <p className="text-sm text-muted-foreground">
              Tokyo shows the strongest price-solar correlation due to high solar capacity. Hokkaido
              experiences more price volatility due to grid isolation and weather patterns.
            </p>
          </div>
        </div>
      </section>

      {/* Data Sources Footer */}
      <section className="rounded-lg border bg-muted/50 p-6">
        <h3 className="font-medium mb-3">Data Sources</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-muted-foreground">
          <div>
            <strong className="text-foreground">JEPX Spot Market</strong>
            <p>30-minute electricity prices for 9 Japanese power areas</p>
          </div>
          <div>
            <strong className="text-foreground">Open-Meteo Archive</strong>
            <p>Hourly solar radiation (GHI, DNI, DHI) from satellite data</p>
          </div>
          <div>
            <strong className="text-foreground">ML Features</strong>
            <p>XGBoost-based forecasting with engineered temporal features</p>
          </div>
        </div>
      </section>
    </div>
  )
}
