/**
 * RUL Card Component
 * Displays RUL prediction with confidence and risk level
 */
import { TrendingDown, AlertTriangle, Clock } from 'lucide-react'

interface RULCardProps {
  rulDays: number
  confidence: number
  riskLevel: 'normal' | 'warning' | 'critical'
  loading?: boolean
}

const riskConfig = {
  normal: {
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    icon: Clock,
    label: 'Healthy',
    message: 'Battery is performing within normal parameters',
  },
  warning: {
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    icon: AlertTriangle,
    label: 'Monitor',
    message: 'Schedule maintenance within 90-180 days',
  },
  critical: {
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    icon: AlertTriangle,
    label: 'Replace Soon',
    message: 'Replacement recommended within 90 days',
  },
}

export default function RULCard({ rulDays, confidence, riskLevel, loading }: RULCardProps) {
  const config = riskConfig[riskLevel]
  const Icon = config.icon

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6 animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-1/2 mb-4"></div>
        <div className="h-12 bg-gray-200 rounded w-3/4 mb-4"></div>
        <div className="h-4 bg-gray-200 rounded w-full"></div>
      </div>
    )
  }

  return (
    <div className={`bg-white rounded-lg shadow p-6 border-2 ${config.borderColor}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          Remaining Useful Life (RUL)
        </h3>
        <Icon className={`h-6 w-6 ${config.color}`} />
      </div>

      <div className="mb-4">
        <div className="flex items-baseline space-x-2">
          <span className="text-4xl font-bold text-gray-900">{Math.round(rulDays)}</span>
          <span className="text-xl text-gray-600">days</span>
        </div>
        <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium mt-2 ${config.bgColor} ${config.color}`}>
          {config.label}
        </div>
      </div>

      <div className="space-y-3">
        <div>
          <div className="flex justify-between text-sm mb-1">
            <span className="text-gray-600">Confidence</span>
            <span className="font-medium text-gray-900">{(confidence * 100).toFixed(0)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all"
              style={{ width: `${confidence * 100}%` }}
            />
          </div>
        </div>

        <div className={`p-3 rounded-lg ${config.bgColor}`}>
          <p className={`text-sm ${config.color}`}>{config.message}</p>
        </div>
      </div>

      <p className="text-xs text-gray-500 mt-4">
        Last updated: {new Date().toLocaleString()}
      </p>
    </div>
  )
}
