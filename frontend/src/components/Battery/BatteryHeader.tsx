/**
 * Battery Header Component
 * Shows battery ID, status badge, and key metrics
 */
import { ArrowLeft } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

interface BatteryHeaderProps {
  batteryId: string
  status: 'healthy' | 'warning' | 'critical'
  soh: number
  locationName?: string
}

const statusColors = {
  healthy: 'bg-green-100 text-green-800 border-green-300',
  warning: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  critical: 'bg-red-100 text-red-800 border-red-300',
}

export default function BatteryHeader({ batteryId, status, soh, locationName }: BatteryHeaderProps) {
  const navigate = useNavigate()

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <button
        onClick={() => navigate(-1)}
        className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
      >
        <ArrowLeft className="h-4 w-4 mr-1" />
        Back
      </button>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{batteryId}</h1>
          {locationName && (
            <p className="text-sm text-gray-600 mt-1">{locationName}</p>
          )}
        </div>

        <div className="flex items-center space-x-4">
          <div className={`px-3 py-1 rounded-full border font-medium text-sm ${statusColors[status]}`}>
            {status.toUpperCase()}
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600">SOH</p>
            <p className="text-2xl font-bold text-gray-900">{soh.toFixed(1)}%</p>
          </div>
        </div>
      </div>
    </div>
  )
}
