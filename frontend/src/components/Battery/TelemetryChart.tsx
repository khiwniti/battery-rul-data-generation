/**
 * Telemetry Chart Component
 * Recharts line chart for battery telemetry data
 */
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { format } from 'date-fns'

interface TelemetryChartProps {
  data: Array<{
    timestamp: string
    value: number
  }>
  title: string
  dataKey: string
  color?: string
  unit?: string
  height?: number
}

export default function TelemetryChart({
  data,
  title,
  dataKey,
  color = '#3b82f6',
  unit = '',
  height = 300,
}: TelemetryChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
        <div className="flex items-center justify-center h-64 text-gray-400">
          <p>No data available</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="timestamp"
            tickFormatter={(value) => format(new Date(value), 'HH:mm')}
            style={{ fontSize: '12px' }}
          />
          <YAxis
            style={{ fontSize: '12px' }}
            label={{ value: unit, angle: -90, position: 'insideLeft' }}
          />
          <Tooltip
            labelFormatter={(value) => format(new Date(value), 'MMM dd, HH:mm')}
            formatter={(value: number) => [`${value.toFixed(2)} ${unit}`, dataKey]}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={2}
            dot={false}
            name={dataKey}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
