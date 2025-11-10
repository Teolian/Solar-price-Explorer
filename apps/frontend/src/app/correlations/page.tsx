'use client'

import { useState } from 'react'
import { api, type CorrelationResult } from '@/lib/api'

const AREAS = [
  'HOKKAIDO', 'TOHOKU', 'TOKYO', 'CHUBU', 'HOKURIKU',
  'KANSAI', 'CHUGOKU', 'SHIKOKU', 'KYUSHU'
]

const PERIODS = ['7d', '14d', '30d', '60d', '90d']

export default function CorrelationsPage() {
  const [selectedArea, setSelectedArea] = useState('TOKYO')
  const [selectedPeriod, setSelectedPeriod] = useState('30d')
  const [correlation, setCorrelation] = useState<CorrelationResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchCorrelations = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await api.getCorrelations(selectedArea, selectedPeriod)
      setCorrelation(result)
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
    </div>
  )
}
