/**
 * LocationGrid Component
 * Displays grid of location cards with battery and alert counts
 */
import { useNavigate } from 'react-router-dom'
import { MapPin, Battery, AlertTriangle } from 'lucide-react'

interface Location {
  location_id: string
  location_name: string
  region: string
  battery_count?: number
  alert_count?: number
}

interface LocationGridProps {
  locations: Location[]
  loading?: boolean
}

export default function LocationGrid({ locations, loading }: LocationGridProps) {
  const navigate = useNavigate()

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(9)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-3/4 mb-4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    )
  }

  if (!locations || locations.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-12 text-center">
        <MapPin className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600">No locations found</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {locations.map((location) => (
        <button
          key={location.location_id}
          onClick={() => navigate(`/location/${location.location_id}`)}
          className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6 text-left"
        >
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                {location.location_name}
              </h3>
              <p className="text-sm text-gray-600 capitalize">{location.region}</p>
            </div>
            <MapPin className="h-5 w-5 text-blue-500" />
          </div>

          <div className="space-y-2">
            <div className="flex items-center text-sm text-gray-700">
              <Battery className="h-4 w-4 mr-2 text-gray-400" />
              <span>{location.battery_count || 0} batteries</span>
            </div>

            {location.alert_count !== undefined && location.alert_count > 0 && (
              <div className="flex items-center text-sm text-red-600">
                <AlertTriangle className="h-4 w-4 mr-2" />
                <span>{location.alert_count} active alerts</span>
              </div>
            )}
          </div>
        </button>
      ))}
    </div>
  )
}
