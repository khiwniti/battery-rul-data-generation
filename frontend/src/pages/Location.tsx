/**
 * Location Page
 * Real-time battery monitoring for a specific location
 */
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { MapPin, Battery, AlertTriangle, TrendingUp, Activity } from 'lucide-react'
import { api } from '@/services/api'
import BatteryTable from '@/components/Location/BatteryTable'
import StatCard from '@/components/Dashboard/StatCard'

export default function LocationPage() {
  const { locationId } = useParams<{ locationId: string }>()

  // Fetch location details
  const { data: location, isLoading: locationLoading } = useQuery({
    queryKey: ['location', locationId],
    queryFn: async () => {
      const response = await api.locations.get(locationId!)
      return response.data
    },
    enabled: !!locationId,
  })

  // Fetch batteries at this location
  const { data: batteriesData, isLoading: batteriesLoading } = useQuery({
    queryKey: ['batteries', locationId],
    queryFn: async () => {
      const response = await api.batteries.list({ location_id: locationId })
      return response.data
    },
    enabled: !!locationId,
  })

  // Fetch active alerts for this location
  const { data: alertsData } = useQuery({
    queryKey: ['alerts', locationId],
    queryFn: async () => {
      const response = await api.alerts.list({ location_id: locationId, active: true })
      return response.data
    },
    enabled: !!locationId,
  })

  if (locationLoading) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow p-6 animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/4"></div>
        </div>
      </div>
    )
  }

  if (!location) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-600">Location not found</p>
      </div>
    )
  }

  // Calculate statistics
  const totalBatteries = batteriesData?.length || 0
  const activeAlerts = alertsData?.filter((a: any) => !a.acknowledged).length || 0
  const criticalBatteries = batteriesData?.filter((b: any) => (b.soh_pct || 100) < 80).length || 0
  const avgSOH = batteriesData?.length
    ? (batteriesData.reduce((sum: number, b: any) => sum + (b.soh_pct || 100), 0) / batteriesData.length).toFixed(1)
    : '100.0'

  return (
    <div className="space-y-6">
      {/* Location Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center space-x-3 mb-2">
              <MapPin className="h-6 w-6 text-blue-500" />
              <h1 className="text-3xl font-bold text-gray-900">{location.location_name}</h1>
            </div>
            <div className="flex items-center space-x-4 text-sm text-gray-600">
              <span className="capitalize">Region: {location.region}</span>
              {location.address && <span>{location.address}</span>}
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600">Location ID</p>
            <p className="text-lg font-semibold text-gray-900">{location.location_id}</p>
          </div>
        </div>

        {/* Location metadata */}
        {location.climate_zone && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <p className="text-gray-600">Climate Zone</p>
                <p className="font-medium text-gray-900 capitalize">{location.climate_zone}</p>
              </div>
              <div>
                <p className="text-gray-600">Typical Temp Range</p>
                <p className="font-medium text-gray-900">
                  {location.region === 'northern' && '20-35°C'}
                  {location.region === 'northeastern' && '22-38°C'}
                  {location.region === 'central' && '24-38°C'}
                  {location.region === 'eastern' && '24-35°C'}
                  {location.region === 'southern' && '25-33°C'}
                </p>
              </div>
              <div>
                <p className="text-gray-600">Season</p>
                <p className="font-medium text-gray-900">
                  {new Date().getMonth() >= 2 && new Date().getMonth() <= 4 && 'Hot (Mar-May)'}
                  {new Date().getMonth() >= 5 && new Date().getMonth() <= 9 && 'Rainy (Jun-Oct)'}
                  {(new Date().getMonth() >= 10 || new Date().getMonth() <= 1) && 'Cool (Nov-Feb)'}
                </p>
              </div>
              <div>
                <p className="text-gray-600">Battery Strings</p>
                <p className="font-medium text-gray-900">9 strings (24 batteries each)</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Batteries"
          value={totalBatteries}
          icon={Battery}
          color="blue"
        />

        <StatCard
          title="Active Alerts"
          value={activeAlerts}
          icon={AlertTriangle}
          color={activeAlerts > 0 ? 'red' : 'green'}
        />

        <StatCard
          title="Critical Batteries"
          value={criticalBatteries}
          icon={Activity}
          color={criticalBatteries > 0 ? 'yellow' : 'green'}
        />

        <StatCard
          title="Average SOH"
          value={`${avgSOH}%`}
          icon={TrendingUp}
          color="green"
        />
      </div>

      {/* Battery Table */}
      <div>
        <div className="mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Battery Status</h2>
          <p className="text-sm text-gray-600 mt-1">
            Real-time monitoring of {totalBatteries} batteries across 9 strings
          </p>
        </div>
        <BatteryTable batteries={batteriesData || []} loading={batteriesLoading} />
      </div>

      {/* Environmental info note */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <Activity className="h-5 w-5 text-blue-600 mt-0.5" />
          <div>
            <h4 className="text-sm font-semibold text-blue-900 mb-1">
              Thai Data Center Environment
            </h4>
            <p className="text-sm text-blue-800">
              This location's battery health is influenced by {location.region} region climate patterns,
              including seasonal temperature variations and monsoon-related power grid stability.
              Battery RUL predictions account for these environmental factors using 15+ years of
              Thai facility engineering data.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
