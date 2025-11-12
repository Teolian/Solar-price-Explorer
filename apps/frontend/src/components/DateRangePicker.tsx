'use client'

import { useState } from 'react'

interface DateRangePickerProps {
  onRangeChange: (startDate: Date, endDate: Date) => void
  defaultDays?: number
  maxDays?: number
}

export function DateRangePicker({
  onRangeChange,
  defaultDays = 30,
  maxDays = 365
}: DateRangePickerProps) {
  const [rangeType, setRangeType] = useState<'preset' | 'custom'>('preset')
  const [presetDays, setPresetDays] = useState(defaultDays.toString())
  const [customStart, setCustomStart] = useState('')
  const [customEnd, setCustomEnd] = useState('')

  const presetOptions = [
    { value: '7', label: 'Last 7 Days' },
    { value: '14', label: 'Last 14 Days' },
    { value: '30', label: 'Last 30 Days' },
    { value: '60', label: 'Last 60 Days' },
    { value: '90', label: 'Last 90 Days' },
  ]

  const handlePresetChange = (days: string) => {
    setPresetDays(days)
    const endDate = new Date()
    const startDate = new Date()
    startDate.setDate(startDate.getDate() - parseInt(days))
    onRangeChange(startDate, endDate)
  }

  const handleCustomApply = () => {
    if (customStart && customEnd) {
      const startDate = new Date(customStart)
      const endDate = new Date(customEnd)

      // Validate date range
      if (startDate > endDate) {
        alert('Start date must be before end date')
        return
      }

      const daysDiff = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24))
      if (daysDiff > maxDays) {
        alert(`Date range cannot exceed ${maxDays} days`)
        return
      }

      onRangeChange(startDate, endDate)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-4">
        <label className="flex items-center space-x-2">
          <input
            type="radio"
            name="rangeType"
            value="preset"
            checked={rangeType === 'preset'}
            onChange={() => setRangeType('preset')}
            className="form-radio"
          />
          <span className="text-sm font-medium">Preset Range</span>
        </label>
        <label className="flex items-center space-x-2">
          <input
            type="radio"
            name="rangeType"
            value="custom"
            checked={rangeType === 'custom'}
            onChange={() => setRangeType('custom')}
            className="form-radio"
          />
          <span className="text-sm font-medium">Custom Range</span>
        </label>
      </div>

      {rangeType === 'preset' ? (
        <div className="flex items-center space-x-4">
          <label className="text-sm font-medium">Period:</label>
          <select
            className="flex-1 p-2 border rounded-md"
            value={presetDays}
            onChange={(e) => handlePresetChange(e.target.value)}
          >
            {presetOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Start Date</label>
              <input
                type="date"
                className="w-full p-2 border rounded-md"
                value={customStart}
                onChange={(e) => setCustomStart(e.target.value)}
                max={customEnd || undefined}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">End Date</label>
              <input
                type="date"
                className="w-full p-2 border rounded-md"
                value={customEnd}
                onChange={(e) => setCustomEnd(e.target.value)}
                min={customStart || undefined}
                max={new Date().toISOString().split('T')[0]}
              />
            </div>
          </div>
          <button
            onClick={handleCustomApply}
            disabled={!customStart || !customEnd}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50"
          >
            Apply Custom Range
          </button>
        </div>
      )}
    </div>
  )
}
