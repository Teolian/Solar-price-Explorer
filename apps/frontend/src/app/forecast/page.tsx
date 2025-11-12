'use client'

import { useState } from 'react'
import { api, type ForecastResponse } from '@/lib/api'
import { useI18n } from '@/lib/i18n'
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
  const { t } = useI18n()
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
        <h1 className="text-3xl font-bold">{t('forecast.title')}</h1>
        <p className="text-muted-foreground">
          {t('forecast.subtitle')}
        </p>
      </div>

      {/* Info Alert */}
      <div className="rounded-lg border border-blue-200 bg-blue-50 dark:bg-blue-950 p-6">
        <h3 className="text-lg font-semibold mb-3 uppercase text-sm tracking-wide text-blue-700 dark:text-blue-300">{t('forecast.training_required')}</h3>

        <div className="space-y-4">
          <p className="text-sm text-muted-foreground">
            {t('forecast.training_desc')}
          </p>

          <div className="p-4 bg-white dark:bg-slate-900 rounded-lg">
            <h4 className="text-sm font-semibold mb-2">{t('forecast.how_to_train')}</h4>
            <div className="space-y-2 text-sm text-muted-foreground">
              <p><strong>{t('forecast.option_api')}</strong></p>
              <pre className="bg-slate-100 dark:bg-slate-800 p-3 rounded text-xs overflow-x-auto">
{`curl -X POST "http://localhost:8000/api/train" \\
  -H "Content-Type: application/json" \\
  -d '{
    "area": "TOKYO",
    "target": "area_price",
    "features": ["ghi", "dni", "dhi", "volume_kwh",
                 "price_lag_1h", "price_lag_24h",
                 "hour", "dow", "month"],
    "val_window": "7d"
  }'`}
              </pre>

              <p className="mt-3"><strong>{t('forecast.option_python')}</strong></p>
              <pre className="bg-slate-100 dark:bg-slate-800 p-3 rounded text-xs overflow-x-auto">
{`import requests

response = requests.post(
    "http://localhost:8000/api/train",
    json={
        "area": "TOKYO",
        "target": "area_price",
        "features": ["ghi", "dni", "dhi", "hour", "dow"],
        "val_window": "7d"
    }
)
print(response.json())`}
              </pre>
            </div>
          </div>

          <div className="p-4 bg-amber-50 dark:bg-amber-950 rounded-lg">
            <h4 className="text-sm font-semibold mb-2 text-amber-700 dark:text-amber-300">{t('forecast.requirements')}</h4>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• {t('forecast.req_price_data')}</li>
              <li>• {t('forecast.req_solar_data')}</li>
              <li>• {t('forecast.req_ml_features')}</li>
              <li>• {t('forecast.req_data_volume')}</li>
            </ul>
          </div>

          <p className="text-xs text-muted-foreground">
            {t('forecast.training_note')}
          </p>
        </div>
      </div>

      <div className="rounded-lg border bg-card p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium mb-2">{t('common.area')}</label>
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
            <label className="block text-sm font-medium mb-2">{t('forecast.horizon')}</label>
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
          {loading ? t('forecast.generating') : t('forecast.generate_button')}
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
            <h2 className="text-xl font-semibold mb-4">{t('forecast.results')}</h2>
            <MultiSeriesChart
              title={`${t('forecast.title')} - ${forecast.area}`}
              series={[
                {
                  name: t('forecast.predicted_price'),
                  data: forecast.points.map((p) => ({
                    timestamp: p.timestamp,
                    value: p.price_pred,
                  })),
                  color: '#3b82f6',
                },
              ]}
              yAxisLabel={t('chart.price_jpy_kwh')}
              height={450}
            />
          </div>

          <div className="rounded-lg border bg-card p-6">
            <h3 className="font-semibold mb-4">{t('forecast.forecast_data')}</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2">{t('data.timestamp')}</th>
                    <th className="text-right p-2">{t('forecast.predicted_price')} (JPY/kWh)</th>
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
                {t('forecast.showing_hours', { total: forecast.points.length })}
              </p>
            )}
          </div>

          <div className="rounded-lg border bg-muted p-4">
            <p className="text-sm">
              <strong>{t('forecast.model')}:</strong> {forecast.model_id}
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              {t('forecast.model_note')}
            </p>
          </div>
        </>
      )}
    </div>
  )
}
