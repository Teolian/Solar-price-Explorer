'use client'

import { useState } from 'react'
import { api, type PricePoint, type RadiationPoint } from '@/lib/api'
import { useI18n } from '@/lib/i18n'
import { formatDate, formatNumber } from '@/lib/utils'
import { TimeSeriesChart, MultiSeriesChart } from '@/components/charts'

const AREAS = [
  'HOKKAIDO', 'TOHOKU', 'TOKYO', 'CHUBU', 'HOKURIKU',
  'KANSAI', 'CHUGOKU', 'SHIKOKU', 'KYUSHU'
]

type DataType = 'prices' | 'radiation'

export default function DataPage() {
  const { t } = useI18n()
  const [selectedArea, setSelectedArea] = useState('TOKYO')
  const [dataType, setDataType] = useState<DataType>('prices')
  const [prices, setPrices] = useState<PricePoint[]>([])
  const [radiation, setRadiation] = useState<RadiationPoint[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      if (dataType === 'prices') {
        const result = await api.getPrices(selectedArea)
        setPrices(result)
        setRadiation([])
      } else {
        const result = await api.getRadiation(selectedArea)
        setRadiation(result)
        setPrices([])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch data')
    } finally {
      setLoading(false)
    }
  }

  const exportData = () => {
    const baseUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'
    const kind = dataType === 'prices' ? 'raw' : 'raw'
    const url = `${baseUrl}/api/export?area=${selectedArea}&kind=${kind}&format=csv`
    window.open(url, '_blank')
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">{t('data.title')}</h1>
        <p className="text-muted-foreground">
          {t('data.subtitle')}
        </p>
      </div>

      <div className="rounded-lg border bg-card p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
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
            <label className="block text-sm font-medium mb-2">{t('data.data_type')}</label>
            <select
              className="w-full p-2 border rounded-md"
              value={dataType}
              onChange={(e) => setDataType(e.target.value as DataType)}
            >
              <option value="prices">{t('overview.price')}</option>
              <option value="radiation">{t('overview.radiation')}</option>
            </select>
          </div>

          <div className="flex items-end gap-2">
            <button
              className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
              onClick={fetchData}
              disabled={loading}
            >
              {loading ? t('common.loading') : t('data.load_data')}
            </button>
            <button
              className="px-4 py-2 border rounded-md hover:bg-accent disabled:opacity-50"
              onClick={exportData}
              disabled={loading}
            >
              {t('data.export_csv')}
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-destructive bg-destructive/10 p-4">
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}

      {prices.length > 0 && (
        <div className="space-y-6">
          {/* Price Chart */}
          <div className="rounded-lg border bg-card p-6">
            <TimeSeriesChart
              title={`${t('data.electricity_prices')} - ${selectedArea}`}
              data={prices.map((p) => ({
                timestamp: p.timestamp,
                value: p.price_jpy_kwh,
              }))}
              yAxisLabel={t('chart.price_jpy_kwh')}
              height={400}
            />
            <p className="text-sm text-muted-foreground mt-4 text-center">
              {t('data.interactive_chart')}
            </p>
          </div>

          {/* Price Table */}
          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-xl font-semibold mb-4">
              {t('data.price_data')} - {selectedArea}
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">{t('data.timestamp')}</th>
                  <th className="text-right p-2">{t('chart.price_jpy_kwh')}</th>
                  <th className="text-right p-2">{t('data.volume')}</th>
                </tr>
              </thead>
              <tbody>
                {prices.slice(0, 100).map((price, idx) => (
                  <tr key={idx} className="border-b">
                    <td className="p-2">{formatDate(price.timestamp)}</td>
                    <td className="text-right p-2">
                      {formatNumber(price.price_jpy_kwh, 2)}
                    </td>
                    <td className="text-right p-2">
                      {price.volume_kwh
                        ? formatNumber(price.volume_kwh, 0)
                        : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {prices.length > 100 && (
            <p className="text-sm text-muted-foreground mt-4">
              {t('data.showing_records', { count: prices.length })}
            </p>
          )}
          </div>
        </div>
      )}

      {radiation.length > 0 && (
        <div className="space-y-6">
          {/* Radiation Chart */}
          <div className="rounded-lg border bg-card p-6">
            <MultiSeriesChart
              title={`${t('data.solar_radiation')} - ${selectedArea}`}
              series={[
                {
                  name: t('data.ghi_global'),
                  data: radiation.map((r) => ({
                    timestamp: r.timestamp,
                    value: r.ghi || 0,
                  })),
                  color: '#f59e0b', // amber
                },
                {
                  name: t('data.dni_direct'),
                  data: radiation.map((r) => ({
                    timestamp: r.timestamp,
                    value: r.dni || 0,
                  })),
                  color: '#ef4444', // red
                },
                {
                  name: t('data.dhi_diffuse'),
                  data: radiation.map((r) => ({
                    timestamp: r.timestamp,
                    value: r.dhi || 0,
                  })),
                  color: '#3b82f6', // blue
                },
              ]}
              yAxisLabel={t('chart.solar_radiation')}
              height={400}
            />
            <p className="text-sm text-muted-foreground mt-4 text-center">
              {t('data.radiation_explanation')}
            </p>
          </div>

          {/* Radiation Table */}
          <div className="rounded-lg border bg-card p-6">
            <h2 className="text-xl font-semibold mb-4">
              {t('data.radiation_data')} - {selectedArea}
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">{t('data.timestamp')}</th>
                  <th className="text-left p-2">{t('data.station')}</th>
                  <th className="text-right p-2">GHI</th>
                  <th className="text-right p-2">DNI</th>
                  <th className="text-right p-2">DHI</th>
                </tr>
              </thead>
              <tbody>
                {radiation.slice(0, 100).map((rad, idx) => (
                  <tr key={idx} className="border-b">
                    <td className="p-2">{formatDate(rad.timestamp)}</td>
                    <td className="p-2">{rad.station}</td>
                    <td className="text-right p-2">
                      {rad.ghi ? formatNumber(rad.ghi, 1) : 'N/A'}
                    </td>
                    <td className="text-right p-2">
                      {rad.dni ? formatNumber(rad.dni, 1) : 'N/A'}
                    </td>
                    <td className="text-right p-2">
                      {rad.dhi ? formatNumber(rad.dhi, 1) : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {radiation.length > 100 && (
            <p className="text-sm text-muted-foreground mt-4">
              {t('data.showing_records', { count: radiation.length })}
            </p>
          )}
          </div>
        </div>
      )}
    </div>
  )
}
