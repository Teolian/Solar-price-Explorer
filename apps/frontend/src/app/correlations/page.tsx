'use client'

import { useState } from 'react'
import { api, type CorrelationResult } from '@/lib/api'
import { ScatterChart } from '@/components/charts'

const AREAS = [
  'HOKKAIDO', 'TOHOKU', 'TOKYO', 'CHUBU', 'HOKURIKU',
  'KANSAI', 'CHUGOKU', 'SHIKOKU', 'KYUSHU'
]

const PERIODS = ['7d', '14d', '30d', '60d', '90d']

interface ScatterData {
  ghi: { x: number; y: number }[]
  dni: { x: number; y: number }[]
  dhi: { x: number; y: number }[]
}

export default function CorrelationsPage() {
  const [selectedArea, setSelectedArea] = useState('TOKYO')
  const [selectedPeriod, setSelectedPeriod] = useState('30d')
  const [correlation, setCorrelation] = useState<CorrelationResult | null>(null)
  const [scatterData, setScatterData] = useState<ScatterData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'ghi' | 'dni' | 'dhi'>('ghi')

  const fetchCorrelations = async () => {
    setLoading(true)
    setError(null)
    setScatterData(null)

    try {
      // Get correlation coefficients
      const result = await api.getCorrelations(selectedArea, selectedPeriod)
      setCorrelation(result)

      // Fetch raw data for scatter plots
      // Calculate date range from period
      const days = parseInt(selectedPeriod.replace('d', ''))
      const endDate = new Date()
      const startDate = new Date()
      startDate.setDate(startDate.getDate() - days)

      const [pricesData, radiationData] = await Promise.all([
        api.getPrices(selectedArea, startDate.toISOString(), endDate.toISOString()),
        api.getRadiation(selectedArea, startDate.toISOString(), endDate.toISOString())
      ])

      // Merge data by timestamp and filter to daytime hours (6-18) like the API does
      const mergedData: Array<{timestamp: string, price: number, ghi: number, dni: number, dhi: number}> = []

      pricesData.forEach((pricePoint) => {
        const radPoint = radiationData.find(
          (r) => r.timestamp === pricePoint.timestamp
        )
        if (radPoint) {
          const hour = new Date(pricePoint.timestamp).getHours()
          // Filter to daytime hours (6am-6pm) for meaningful solar correlation
          if (hour >= 6 && hour <= 18) {
            mergedData.push({
              timestamp: pricePoint.timestamp,
              price: pricePoint.price,
              ghi: radPoint.ghi || 0,
              dni: radPoint.dni || 0,
              dhi: radPoint.dhi || 0,
            })
          }
        }
      })

      // Prepare scatter data for each radiation type
      setScatterData({
        ghi: mergedData.map((d) => ({ x: d.ghi, y: d.price })),
        dni: mergedData.map((d) => ({ x: d.dni, y: d.price })),
        dhi: mergedData.map((d) => ({ x: d.dhi, y: d.price })),
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch correlations')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Correlation Analysis</h1>
        <p className="text-muted-foreground">
          Analyze correlations between solar radiation and electricity prices
        </p>
      </div>

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
            <label className="block text-sm font-medium mb-2">Period</label>
            <select
              className="w-full p-2 border rounded-md"
              value={selectedPeriod}
              onChange={(e) => setSelectedPeriod(e.target.value)}
            >
              {PERIODS.map((period) => (
                <option key={period} value={period}>
                  {period}
                </option>
              ))}
            </select>
          </div>
        </div>

        <button
          className="w-full md:w-auto px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
          onClick={fetchCorrelations}
          disabled={loading}
        >
          {loading ? 'Loading...' : 'Calculate Correlations'}
        </button>
      </div>

      {error && (
        <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}

      {correlation && (
        <div className="rounded-lg border bg-card p-6">
          <h2 className="text-xl font-semibold mb-4">Results</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="rounded-lg border p-4">
              <div className="text-sm text-muted-foreground mb-1">
                GHI ↔ Price
              </div>
              <div className="text-2xl font-bold">
                {correlation.r_ghi?.toFixed(3) ?? 'N/A'}
              </div>
            </div>

            <div className="rounded-lg border p-4">
              <div className="text-sm text-muted-foreground mb-1">
                DNI ↔ Price
              </div>
              <div className="text-2xl font-bold">
                {correlation.r_dni?.toFixed(3) ?? 'N/A'}
              </div>
            </div>

            <div className="rounded-lg border p-4">
              <div className="text-sm text-muted-foreground mb-1">
                DHI ↔ Price
              </div>
              <div className="text-2xl font-bold">
                {correlation.r_dhi?.toFixed(3) ?? 'N/A'}
              </div>
            </div>
          </div>

          <div className="text-sm text-muted-foreground">
            <p>Area: {correlation.area}</p>
            <p>Period: {correlation.period}</p>
            <p>Sample size: {correlation.n} observations</p>
          </div>

          <div className="mt-6 p-4 bg-muted rounded-lg">
            <h3 className="font-medium mb-2">Interpretation</h3>
            <ul className="text-sm space-y-1">
              <li>• Positive correlation: Higher radiation → Higher prices</li>
              <li>• Negative correlation: Higher radiation → Lower prices</li>
              <li>• |r| &gt; 0.5: Strong correlation</li>
              <li>• |r| = 0.3-0.5: Moderate correlation</li>
              <li>• |r| &lt; 0.3: Weak correlation</li>
            </ul>
          </div>
        </div>
      )}

      {/* Scatter Plot Visualization */}
      {scatterData && correlation && (
        <div className="rounded-lg border bg-card p-6">
          <h2 className="text-xl font-semibold mb-4">Visual Analysis</h2>

          {/* Tabs for different radiation types */}
          <div className="flex space-x-2 mb-4 border-b">
            <button
              className={`px-4 py-2 font-medium transition-colors ${
                activeTab === 'ghi'
                  ? 'border-b-2 border-primary text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
              onClick={() => setActiveTab('ghi')}
            >
              GHI (Global)
            </button>
            <button
              className={`px-4 py-2 font-medium transition-colors ${
                activeTab === 'dni'
                  ? 'border-b-2 border-primary text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
              onClick={() => setActiveTab('dni')}
            >
              DNI (Direct)
            </button>
            <button
              className={`px-4 py-2 font-medium transition-colors ${
                activeTab === 'dhi'
                  ? 'border-b-2 border-primary text-primary'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
              onClick={() => setActiveTab('dhi')}
            >
              DHI (Diffuse)
            </button>
          </div>

          {/* Scatter plot based on active tab */}
          <div className="mt-4">
            {activeTab === 'ghi' && scatterData.ghi.length > 0 && (
              <ScatterChart
                title={`${selectedArea}: Solar Radiation (GHI) vs Electricity Price`}
                data={scatterData.ghi}
                xAxisLabel="GHI (W/m²)"
                yAxisLabel="Price (JPY/kWh)"
                height={500}
                showTrendLine={true}
                correlation={correlation.r_ghi}
              />
            )}
            {activeTab === 'dni' && scatterData.dni.length > 0 && (
              <ScatterChart
                title={`${selectedArea}: Direct Radiation (DNI) vs Electricity Price`}
                data={scatterData.dni}
                xAxisLabel="DNI (W/m²)"
                yAxisLabel="Price (JPY/kWh)"
                height={500}
                showTrendLine={true}
                correlation={correlation.r_dni}
              />
            )}
            {activeTab === 'dhi' && scatterData.dhi.length > 0 && (
              <ScatterChart
                title={`${selectedArea}: Diffuse Radiation (DHI) vs Electricity Price`}
                data={scatterData.dhi}
                xAxisLabel="DHI (W/m²)"
                yAxisLabel="Price (JPY/kWh)"
                height={500}
                showTrendLine={true}
                correlation={correlation.r_dhi}
              />
            )}
          </div>

          <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-950 rounded-lg text-sm">
            <p className="font-medium mb-2 uppercase text-xs tracking-wide text-blue-700 dark:text-blue-300">Chart Guide</p>
            <ul className="space-y-1 text-sm">
              <li>• Each point represents one hour of data (daytime hours only: 6am-6pm)</li>
              <li>• The red dashed line shows the trend (regression line)</li>
              <li>• Downward slope = negative correlation (more sun → lower prices)</li>
              <li>• Upward slope = positive correlation (more sun → higher prices)</li>
              <li>• Tighter clustering around line = stronger correlation</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  )
}
