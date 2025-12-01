/**
 * RecentAlerts Component
 * Displays list of recent alerts with severity badges
 */
import { useNavigate } from 'react-router-dom'
import { AlertTriangle, Clock } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

interface Alert {
  alert_id: string
  battery_id: string
  severity: 'info' | 'warning' | 'critical'
  alert_type: string
  message: string
  triggered_at: string
}

interface RecentAlertsProps {
  alerts: Alert[]
  loading?: boolean
}

const severityColors = {
  info: 'bg-blue-100 text-blue-800 border-blue-200',
  warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  critical: 'bg-red-100 text-red-800 border-red-200',
}

export default function RecentAlerts({ alerts, loading }: RecentAlertsProps) {
  const navigate = useNavigate()

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Alerts</h2>
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900">Recent Alerts</h2>
        <button
          onClick={() => navigate('/alerts')}
          className="text-sm text-blue-600 hover:text-blue-700"
        >
          View all
        </button>
      </div>

      {!alerts || alerts.length === 0 ? (
        <div className="text-center py-8">
          <AlertTriangle className="h-12 w-12 text-gray-400 mx-auto mb-3" />
          <p className="text-gray-600">No recent alerts</p>
        </div>
      ) : (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <button
              key={alert.alert_id}
              onClick={() => navigate(`/battery/${alert.battery_id}`)}
              className="w-full text-left p-3 rounded-lg border hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-start justify-between mb-2">
                <span
                  className={`px-2 py-1 text-xs font-medium rounded-full border ${
                    severityColors[alert.severity]
                  }`}
                >
                  {alert.severity.toUpperCase()}
                </span>
                <span className="text-xs text-gray-500 flex items-center">
                  <Clock className="h-3 w-3 mr-1" />
                  {formatDistanceToNow(new Date(alert.triggered_at), { addSuffix: true })}
                </span>
              </div>

              <p className="text-sm font-medium text-gray-900 mb-1">
                {alert.alert_type.replace(/_/g, ' ')}
              </p>
              <p className="text-xs text-gray-600">{alert.message}</p>
              <p className="text-xs text-gray-500 mt-1">Battery: {alert.battery_id}</p>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
