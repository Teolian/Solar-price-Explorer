'use client'

import { useEffect, useState } from 'react'
import { api, SavingsPotentialResponse } from '@/lib/api'
import ReactECharts from 'echarts-for-react'

const AREAS = ['TOKYO', 'KANSAI', 'CHUBU', 'TOHOKU', 'KYUSHU', 'HOKKAIDO', 'CHUGOKU', 'SHIKOKU', 'HOKURIKU']

export default function BusinessPage() {
  const [selectedArea, setSelectedArea] = useState('TOKYO')
  const [savingsData, setSavingsData] = useState<SavingsPotentialResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [customConsumption, setCustomConsumption] = useState<number>(500)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchSavingsData()
  }, [selectedArea])

  const fetchSavingsData = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await api.getSavingsPotential(selectedArea)
      setSavingsData(data)
    } catch (err) {
      console.error('Error fetching savings data:', err)
      setError('Failed to load savings data. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const calculateCustomSavings = () => {
    if (!savingsData) return { monthly: 0, annual: 0 }

    const priceDiff = savingsData.savings_analysis.price_difference
    const shiftPercentage = 0.30 // Assume 30% of consumption can be shifted

    return {
      monthly: Math.round(customConsumption * shiftPercentage * priceDiff * 30),
      annual: Math.round(customConsumption * shiftPercentage * priceDiff * 365)
    }
  }

  const getHourlyPriceChartOption = () => {
    if (!savingsData) return {}

    const analysis = savingsData.savings_analysis

    // Create hourly data with highlights for best/worst hours
    const hours = Array.from({ length: 24 }, (_, i) => i)
    const bestHoursSet = new Set(analysis.best_hours)
    const worstHoursSet = new Set(analysis.worst_hours)

    return {
      title: {
        text: 'Best vs Worst Hours for Energy Consumption',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          const hour = params[0].axisValue
          const isBest = bestHoursSet.has(parseInt(hour))
          const isWorst = worstHoursSet.has(parseInt(hour))
          let label = `Hour: ${hour}:00`
          if (isBest) label += '<br/>✅ BEST TIME (Low Price)'
          if (isWorst) label += '<br/>❌ AVOID (High Price)'
          return label
        }
      },
      xAxis: {
        type: 'category',
        data: hours.map(h => `${h}:00`),
        name: 'Hour of Day'
      },
      yAxis: {
        type: 'value',
        name: 'Price Level'
      },
      series: [
        {
          name: 'Best Hours',
          type: 'bar',
          data: hours.map(h => bestHoursSet.has(h) ? 1 : 0),
          itemStyle: { color: '#10b981' },
          stack: 'total'
        },
        {
          name: 'Worst Hours',
          type: 'bar',
          data: hours.map(h => worstHoursSet.has(h) ? 1 : 0),
          itemStyle: { color: '#ef4444' },
          stack: 'total'
        },
        {
          name: 'Normal Hours',
          type: 'bar',
          data: hours.map(h => (!bestHoursSet.has(h) && !worstHoursSet.has(h)) ? 0.5 : 0),
          itemStyle: { color: '#94a3b8' },
          stack: 'total'
        }
      ],
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      }
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-slate-200 rounded w-1/3 mb-6"></div>
          <div className="space-y-4">
            <div className="h-32 bg-slate-200 rounded"></div>
            <div className="h-32 bg-slate-200 rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <h3 className="text-lg font-semibold text-red-800">Error</h3>
          <p className="text-red-600">{error}</p>
        </div>
      </div>
    )
  }

  if (!savingsData) return null

  const analysis = savingsData.savings_analysis
  const customSavings = calculateCustomSavings()

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Business Value Analysis</h1>
          <p className="text-muted-foreground mt-2">
            Calculate potential savings and optimize your energy consumption strategy
          </p>
        </div>
        <div>
          <label className="text-sm font-medium mr-2">Area:</label>
          <select
            value={selectedArea}
            onChange={(e) => setSelectedArea(e.target.value)}
            className="border rounded px-3 py-2"
          >
            {AREAS.map((area) => (
              <option key={area} value={area}>
                {area}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="rounded-lg border bg-gradient-to-br from-red-50 to-red-100 p-4">
          <h3 className="text-xs font-medium text-red-700 uppercase tracking-wide mb-2">
            Peak Hours Price
          </h3>
          <div className="text-3xl font-bold text-red-900">
            ¥{analysis.peak_price_avg.toFixed(2)}
          </div>
          <p className="text-xs text-red-600 mt-1">per kWh (7-9, 18-20)</p>
        </div>

        <div className="rounded-lg border bg-gradient-to-br from-green-50 to-green-100 p-4">
          <h3 className="text-xs font-medium text-green-700 uppercase tracking-wide mb-2">
            Solar Hours Price
          </h3>
          <div className="text-3xl font-bold text-green-900">
            ¥{analysis.solar_price_avg.toFixed(2)}
          </div>
          <p className="text-xs text-green-600 mt-1">per kWh (10-14)</p>
        </div>

        <div className="rounded-lg border bg-gradient-to-br from-blue-50 to-blue-100 p-4">
          <h3 className="text-xs font-medium text-blue-700 uppercase tracking-wide mb-2">
            Price Difference
          </h3>
          <div className="text-3xl font-bold text-blue-900">
            ¥{analysis.price_difference.toFixed(2)}
          </div>
          <p className="text-xs text-blue-600 mt-1">savings per kWh</p>
        </div>

        <div className="rounded-lg border bg-gradient-to-br from-amber-50 to-amber-100 p-4">
          <h3 className="text-xs font-medium text-amber-700 uppercase tracking-wide mb-2">
            Savings Potential
          </h3>
          <div className="text-3xl font-bold text-amber-900">
            {analysis.savings_percentage.toFixed(1)}%
          </div>
          <p className="text-xs text-amber-600 mt-1">by shifting to solar hours</p>
        </div>
      </div>

      {/* Custom Savings Calculator */}
      <div className="rounded-lg border bg-gradient-to-r from-indigo-50 to-purple-50 p-6">
        <h2 className="text-2xl font-semibold mb-4">Savings Calculator</h2>

        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">
            Daily Energy Consumption (kWh):
          </label>
          <input
            type="number"
            value={customConsumption}
            onChange={(e) => setCustomConsumption(Number(e.target.value))}
            className="border rounded px-4 py-2 w-full max-w-xs"
            min="0"
            step="100"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg p-6 border-2 border-indigo-200">
            <h3 className="text-lg font-semibold text-indigo-900 mb-4">
              Monthly Savings
            </h3>
            <div className="text-4xl font-bold text-indigo-600">
              ¥{customSavings.monthly.toLocaleString()}
            </div>
            <p className="text-sm text-muted-foreground mt-2">
              By shifting 30% of consumption to solar hours
            </p>
          </div>

          <div className="bg-white rounded-lg p-6 border-2 border-purple-200">
            <h3 className="text-lg font-semibold text-purple-900 mb-4">
              Annual Savings
            </h3>
            <div className="text-4xl font-bold text-purple-600">
              ¥{customSavings.annual.toLocaleString()}
            </div>
            <p className="text-sm text-muted-foreground mt-2">
              Estimated yearly savings potential
            </p>
          </div>
        </div>

        <div className="mt-6 p-4 bg-blue-50 rounded border border-blue-200">
          <h4 className="font-semibold text-blue-900 mb-2">Recommendation:</h4>
          <p className="text-blue-800">
            Schedule energy-intensive operations during solar hours (10:00-14:00) to maximize savings.
            Consider installing battery storage to capture cheap solar energy for use during peak hours.
          </p>
        </div>
      </div>

      {/* Example Scenarios */}
      <div className="rounded-lg border p-6">
        <h2 className="text-2xl font-semibold mb-4">Example Scenarios</h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Small Business */}
          <div className="border rounded-lg p-4 bg-slate-50">
            <h3 className="text-xs font-medium text-slate-700 uppercase tracking-wide mb-3">
              Small Business
            </h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Daily Usage:</span>
                <span className="font-medium">
                  {analysis.example_scenarios.small_business.daily_consumption_kwh} kWh
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Monthly Savings:</span>
                <span className="font-semibold text-green-600">
                  ¥{analysis.example_scenarios.small_business.monthly_savings_jpy.toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Annual Savings:</span>
                <span className="font-semibold text-green-700">
                  ¥{analysis.example_scenarios.small_business.annual_savings_jpy.toLocaleString()}
                </span>
              </div>
            </div>
          </div>

          {/* Medium Factory */}
          <div className="border rounded-lg p-4 bg-blue-50">
            <h3 className="text-xs font-medium text-blue-700 uppercase tracking-wide mb-3">
              Medium Factory
            </h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Daily Usage:</span>
                <span className="font-medium">
                  {analysis.example_scenarios.medium_factory.daily_consumption_kwh} kWh
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Monthly Savings:</span>
                <span className="font-semibold text-green-600">
                  ¥{analysis.example_scenarios.medium_factory.monthly_savings_jpy.toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Annual Savings:</span>
                <span className="font-semibold text-green-700">
                  ¥{analysis.example_scenarios.medium_factory.annual_savings_jpy.toLocaleString()}
                </span>
              </div>
            </div>
          </div>

          {/* Large Factory */}
          <div className="border rounded-lg p-4 bg-purple-50">
            <h3 className="text-xs font-medium text-purple-700 uppercase tracking-wide mb-3">
              Large Factory
            </h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Daily Usage:</span>
                <span className="font-medium">
                  {analysis.example_scenarios.large_factory.daily_consumption_kwh} kWh
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Monthly Savings:</span>
                <span className="font-semibold text-green-600">
                  ¥{analysis.example_scenarios.large_factory.monthly_savings_jpy.toLocaleString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-muted-foreground">Annual Savings:</span>
                <span className="font-semibold text-green-700">
                  ¥{analysis.example_scenarios.large_factory.annual_savings_jpy.toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Best Time Recommendations */}
      <div className="rounded-lg border p-6 bg-gradient-to-r from-green-50 to-blue-50">
        <h2 className="text-2xl font-semibold mb-4">Best Time to Buy/Consume Electricity</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Best Times */}
          <div className="bg-white rounded-lg p-6 border-2 border-green-200">
            <h3 className="text-lg font-semibold text-green-900 mb-3 uppercase tracking-wide">
              ✅ Best Times (Low Prices)
            </h3>
            <div className="space-y-3">
              <div className="text-2xl font-bold text-green-600">
                {analysis.best_hours.map(h => `${h}:00`).join(', ')}
              </div>
              <p className="text-sm text-green-800">
                Average price: ¥{analysis.solar_price_avg.toFixed(2)}/kWh
              </p>
              <p className="text-sm text-green-700">
                Savings up to {analysis.savings_percentage.toFixed(0)}% vs peak hours
              </p>
              <div className="mt-4 p-3 bg-green-100 rounded">
                <p className="text-sm font-medium text-green-900">
                  Recommended Actions:
                </p>
                <ul className="mt-2 space-y-1 text-sm text-green-800">
                  <li>• Run manufacturing processes</li>
                  <li>• Charge battery storage systems</li>
                  <li>• Operate heavy machinery</li>
                  <li>• Run HVAC systems (pre-cooling/heating)</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Worst Times */}
          <div className="bg-white rounded-lg p-6 border-2 border-red-200">
            <h3 className="text-lg font-semibold text-red-900 mb-3 uppercase tracking-wide">
              ❌ Avoid Times (High Prices)
            </h3>
            <div className="space-y-3">
              <div className="text-2xl font-bold text-red-600">
                {analysis.worst_hours.map(h => `${h}:00`).join(', ')}
              </div>
              <p className="text-sm text-red-800">
                Average price: ¥{analysis.peak_price_avg.toFixed(2)}/kWh
              </p>
              <p className="text-sm text-red-700">
                Premium +{analysis.savings_percentage.toFixed(0)}% vs solar hours
              </p>
              <div className="mt-4 p-3 bg-red-100 rounded">
                <p className="text-sm font-medium text-red-900">
                  Recommended Actions:
                </p>
                <ul className="mt-2 space-y-1 text-sm text-red-800">
                  <li>• Minimize energy-intensive operations</li>
                  <li>• Use battery storage if available</li>
                  <li>• Delay non-critical processes</li>
                  <li>• Reduce HVAC load</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Hourly Price Chart */}
      <div className="rounded-lg border p-6">
        <h2 className="text-2xl font-semibold mb-4">Hourly Price Optimization Guide</h2>
        <ReactECharts option={getHourlyPriceChartOption()} style={{ height: '400px' }} />
      </div>

      {/* Strategic Actions */}
      <div className="rounded-lg border border-blue-200 bg-blue-50 p-6">
        <h2 className="text-2xl font-semibold text-blue-900 mb-4">Strategic Action Plan</h2>

        <div className="space-y-4">
          <div className="flex items-start">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold">
              1
            </div>
            <div className="ml-4">
              <h3 className="font-semibold text-blue-900">Shift Consumption to Solar Hours</h3>
              <p className="text-blue-800 mt-1">
                Move {(analysis.savings_percentage * 0.3).toFixed(0)}% of energy consumption to 10:00-14:00
                → Save approximately ¥{customSavings.monthly.toLocaleString()}/month
              </p>
            </div>
          </div>

          <div className="flex items-start">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold">
              2
            </div>
            <div className="ml-4">
              <h3 className="font-semibold text-blue-900">Install Battery Storage</h3>
              <p className="text-blue-800 mt-1">
                Capture energy during cheap hours (¥{analysis.solar_price_avg.toFixed(2)}/kWh) and use
                during peak hours. Arbitrage ¥{analysis.price_difference.toFixed(2)}/kWh difference.
              </p>
            </div>
          </div>

          <div className="flex items-start">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold">
              3
            </div>
            <div className="ml-4">
              <h3 className="font-semibold text-blue-900">Monitor JEPX Prices Daily</h3>
              <p className="text-blue-800 mt-1">
                Use this tool to track real-time price patterns and adjust operations accordingly.
                Set up alerts for exceptional price opportunities.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
