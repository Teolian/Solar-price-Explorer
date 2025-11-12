'use client'

import { useState } from 'react'
import { api, type ForecastResponse } from '@/lib/api'
import { MultiSeriesChart } from '@/components/charts'
import { formatDate } from '@/lib/utils'

const AREAS = [
  'HOKKAIDO', 'TOHOKU', 'TOKYO', 'CHUBU', 'HOKURIKU',
  'KANSAI', 'CHUGOKU', 'SHIKOKU', 'KYUSHU'
]

const HORIZONS = [
  { value: 24, label: '24 hours' },
  { value: 48, label: '48 hours' },
  { value: 72, label: '72 hours' },
  { value: 168, label: '1 week' },
]

export default function ForecastPage() {
  const [selectedArea, setSelectedArea] = useState('TOKYO')
  const [selectedHorizon, setSelectedHorizon] = useState(24)
  const [forecast, setForecast] = useState<ForecastResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const generateForecast = async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await api.forecast(selectedArea, selectedHorizon)
      setForecast(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate forecast')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Price Forecast</h1>
        <p className="text-muted-foreground">
          Generate electricity price forecasts using trained ML models
        </p>
      </div>

      {/* Info Alert */}
      <div className="rounded-lg border border-blue-200 bg-blue-50 dark:bg-blue-950 p-4">
        <h3 className="text-sm font-medium mb-2 uppercase tracking-wide text-blue-700 dark:text-blue-300">Model Training Required</h3>
        <p className="text-sm text-muted-foreground mb-2">
          Before generating forecasts, you need to train an ML model using historical data.
        </p>
        <p className="text-xs text-muted-foreground">
          <strong>How to train:</strong> Use the API endpoint <code className="bg-white dark:bg-slate-800 px-1 py-0.5 rounded">/api/train</code> with your area and features.
          Models are trained using XGBoost on historical price and solar radiation data.
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
            <label className="block text-sm font-medium mb-2">Horizon</label>
            <select
              className="w-full p-2 border rounded-md"
              value={selectedHorizon}
              onChange={(e) => setSelectedHorizon(Number(e.target.value))}
            >
              {HORIZONS.map((h) => (
                <option key={h.value} value={h.value}>
                  {h.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <button
          className="w-full md:w-auto px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
          onClick={generateForecast}
          disabled={loading}
        >
          {loading ? 'Generating...' : 'Generate Forecast'}
        </button>
      </div>

      {error && (
        <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}

      {forecast && forecast.points.length > 0 && (
        <>
          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-xl font-semibold mb-4">Forecast Results</h2>
            <MultiSeriesChart
              title={`Price Forecast - ${forecast.area}`}
              series={[
                {
                  name: 'Predicted Price',
                  data: forecast.points.map((p) => ({
                    timestamp: p.timestamp,
                    value: p.price_pred,
                  })),
                  color: '#3b82f6',
                },
              ]}
              yAxisLabel="Price (JPY/kWh)"
              height={450}
            />
          </div>

          <div className="rounded-lg border bg-card p-6">
            <h3 className="font-semibold mb-4">Forecast Data</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">Timestamp (JST)</th>
                    <th className="text-right p-2">Predicted Price (JPY/kWh)</th>
                  </tr>
                </thead>
                <tbody>
                  {forecast.points.slice(0, 24).map((point, idx) => (
                    <tr key={idx} className="border-b">
                      <td className="p-2">{formatDate(point.timestamp)}</td>
                      <td className="text-right p-2">
                        {point.price_pred.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {forecast.points.length > 24 && (
              <p className="text-sm text-muted-foreground mt-2">
                Showing first 24 hours. Total: {forecast.points.length} hours.
              </p>
            )}
          </div>

          <div className="rounded-lg border bg-muted p-4">
            <p className="text-sm">
              <strong>Model:</strong> {forecast.model_id}
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              Forecast generated using XGBoost baseline model. Results are for
              analysis purposes only.
            </p>
          </div>
        </>
      )}
    </div>
  )
}
