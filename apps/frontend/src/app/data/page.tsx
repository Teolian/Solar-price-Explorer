'use client'

import { useState } from 'react'
import { api, type PricePoint, type RadiationPoint } from '@/lib/api'
import { formatDate, formatNumber } from '@/lib/utils'

const AREAS = [
  'HOKKAIDO', 'TOHOKU', 'TOKYO', 'CHUBU', 'HOKURIKU',
  'KANSAI', 'CHUGOKU', 'SHIKOKU', 'KYUSHU'
]

type DataType = 'prices' | 'radiation'

export default function DataPage() {
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
        <h1 className="text-3xl font-bold">Data Explorer</h1>
        <p className="text-muted-foreground">
          Browse and export raw price and radiation data
        </p>
      </div>

      <div className="rounded-lg border bg-card p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
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
            <label className="block text-sm font-medium mb-2">Data Type</label>
            <select
              className="w-full p-2 border rounded-md"
              value={dataType}
              onChange={(e) => setDataType(e.target.value as DataType)}
            >
              <option value="prices">Prices</option>
              <option value="radiation">Radiation</option>
            </select>
          </div>

          <div className="flex items-end gap-2">
            <button
              className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
              onClick={fetchData}
              disabled={loading}
            >
              {loading ? 'Loading...' : 'Load Data'}
            </button>
            <button
              className="px-4 py-2 border rounded-md hover:bg-accent disabled:opacity-50"
              onClick={exportData}
              disabled={loading}
            >
              Export CSV
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
        <div className="rounded-lg border bg-card p-6">
          <h2 className="text-xl font-semibold mb-4">
            Price Data - {selectedArea}
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Timestamp (JST)</th>
                  <th className="text-right p-2">Price (JPY/kWh)</th>
                  <th className="text-right p-2">Volume (kWh)</th>
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
              Showing first 100 of {prices.length} records. Export to view all.
            </p>
          )}
        </div>
      )}

      {radiation.length > 0 && (
        <div className="rounded-lg border bg-card p-6">
          <h2 className="text-xl font-semibold mb-4">
            Radiation Data - {selectedArea}
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Timestamp (JST)</th>
                  <th className="text-left p-2">Station</th>
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
              Showing first 100 of {radiation.length} records. Export to view
              all.
            </p>
          )}
        </div>
      )}
    </div>
  )
}
