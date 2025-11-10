const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

export interface Area {
  areas: string[]
}

export interface PricePoint {
  timestamp: string
  area: string
  price_jpy_kwh: number
  volume_kwh?: number
}

export interface RadiationPoint {
  timestamp: string
  station: string
  area: string
  ghi?: number
  dni?: number
  dhi?: number
}

export interface CorrelationResult {
  area: string
  period: string
  n: number
  r_ghi?: number
  r_dni?: number
  r_dhi?: number
}

export interface ForecastPoint {
  timestamp: string
  price_pred: number
  p10?: number
  p90?: number
}

export interface ForecastResponse {
  area: string
  model_id: string
  points: ForecastPoint[]
}

export const api = {
  async getAreas(): Promise<Area> {
    const res = await fetch(`${API_BASE}/api/areas`)
    if (!res.ok) throw new Error('Failed to fetch areas')
    return res.json()
  },

  async getPrices(
    area: string,
    from?: string,
    to?: string
  ): Promise<PricePoint[]> {
    const params = new URLSearchParams({ area })
    if (from) params.append('from', from)
    if (to) params.append('to', to)

    const res = await fetch(`${API_BASE}/api/prices?${params}`)
    if (!res.ok) throw new Error('Failed to fetch prices')
    const data = await res.json()
    return data.data || []
  },

  async getRadiation(
    area: string,
    from?: string,
    to?: string
  ): Promise<RadiationPoint[]> {
    const params = new URLSearchParams({ area })
    if (from) params.append('from', from)
    if (to) params.append('to', to)

    const res = await fetch(`${API_BASE}/api/radiation?${params}`)
    if (!res.ok) throw new Error('Failed to fetch radiation')
    const data = await res.json()
    return data.data || []
  },

  async getCorrelations(
    area: string,
    period: string = '30d'
  ): Promise<CorrelationResult> {
    const params = new URLSearchParams({ area, period })
    const res = await fetch(`${API_BASE}/api/corr?${params}`)
    if (!res.ok) throw new Error('Failed to fetch correlations')
    return res.json()
  },

  async forecast(
    area: string,
    horizon_hours: number = 24
  ): Promise<ForecastResponse> {
    const res = await fetch(`${API_BASE}/api/forecast`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ area, horizon_hours }),
    })
    if (!res.ok) throw new Error('Failed to generate forecast')
    return res.json()
  },
}
