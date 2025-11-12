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

export interface HourlyPattern {
  hour: number
  avg_price: number
  avg_ghi: number
  avg_dni?: number
  avg_dhi?: number
  count: number
}

export interface HourlyPatternsResponse {
  area: string
  date_range: {
    from: string
    to: string
  }
  patterns: HourlyPattern[]
}

export interface AreaStats {
  area: string
  avg_price: number
  min_price: number
  max_price: number
  avg_ghi: number
  correlation?: number
  data_points: number
}

export interface MultiAreaComparisonResponse {
  date_range: {
    from: string
    to: string
  }
  areas: AreaStats[]
}

export interface StatsSummary {
  area: string
  date_range: {
    from: string
    to: string
  }
  price_stats: {
    avg: number
    min: number
    max: number
    std: number
  }
  radiation_stats: {
    avg_ghi: number
    min_ghi: number
    max_ghi: number
    avg_dni: number
    avg_dhi: number
  }
  correlation?: number
  top_expensive_hours: Array<{
    timestamp: string
    price: number
  }>
  top_cheap_hours: Array<{
    timestamp: string
    price: number
  }>
  total_records: number
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

  async getHourlyPatterns(
    area: string,
    from?: string,
    to?: string
  ): Promise<HourlyPatternsResponse> {
    const params = new URLSearchParams({ area })
    if (from) params.append('from_date', from)
    if (to) params.append('to_date', to)

    const res = await fetch(`${API_BASE}/api/stats/hourly-patterns?${params}`)
    if (!res.ok) throw new Error('Failed to fetch hourly patterns')
    return res.json()
  },

  async getMultiAreaComparison(
    areas: string[],
    from?: string,
    to?: string
  ): Promise<MultiAreaComparisonResponse> {
    const params = new URLSearchParams({ areas: areas.join(',') })
    if (from) params.append('from_date', from)
    if (to) params.append('to_date', to)

    const res = await fetch(`${API_BASE}/api/stats/multi-area-comparison?${params}`)
    if (!res.ok) throw new Error('Failed to fetch multi-area comparison')
    return res.json()
  },

  async getStatsSummary(
    area: string,
    from?: string,
    to?: string
  ): Promise<StatsSummary> {
    const params = new URLSearchParams({ area })
    if (from) params.append('from_date', from)
    if (to) params.append('to_date', to)

    const res = await fetch(`${API_BASE}/api/stats/summary?${params}`)
    if (!res.ok) throw new Error('Failed to fetch stats summary')
    return res.json()
  },
}
