/**
 * Dashboard Page
 * Overview of all locations with battery health summary
 */
import { useQuery } from '@tanstack/react-query'
import { Battery, AlertTriangle, Activity, TrendingUp } from 'lucide-react'
import { api } from '@/services/api'
import StatCard from '@/components/Dashboard/StatCard'
import LocationGrid from '@/components/Dashboard/LocationGrid'
import RecentAlerts from '@/components/Dashboard/RecentAlerts'

export default function DashboardPage() {
  // Fetch locations
  const { data: locationsData, isLoading: locationsLoading } = useQuery({
    queryKey: ['locations'],
    queryFn: async () => {
      const response = await api.locations.list()
      return response.data
    },
  })

  // Fetch batteries summary
  const { data: batteriesData, isLoading: batteriesLoading } = useQuery({
    queryKey: ['batteries'],
    queryFn: async () => {
      const response = await api.batteries.list()
      return response.data
    },
  })

  // Fetch recent alerts
  const { data: alertsData, isLoading: alertsLoading } = useQuery({
    queryKey: ['alerts-recent'],
    queryFn: async () => {
      const response = await api.alerts.list({ active: true })
      return response.data
    },
  })

  // Calculate stats
  const totalBatteries = batteriesData?.length || 0
  const activeAlerts = alertsData?.filter((a: any) => a.acknowledged === false).length || 0
  const criticalBatteries = batteriesData?.filter((b: any) => b.soh_pct < 80).length || 0
  const avgSOH = batteriesData?.length
    ? (batteriesData.reduce((sum: number, b: any) => sum + (b.soh_pct || 100), 0) / batteriesData.length).toFixed(1)
    : '100.0'

  return (
    <div className="space-y-6">
      {/* Page title */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">
          Battery Health Dashboard
        </h1>
        <p className="text-gray-600 mt-1">
          Monitor battery health across 9 Thai data centers
        </p>
      </div>

      {/* Stat cards */}
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

      {/* Location grid */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Locations</h2>
        <LocationGrid locations={locationsData || []} loading={locationsLoading} />
      </div>

      {/* Recent alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RecentAlerts alerts={alertsData?.slice(0, 10) || []} loading={alertsLoading} />

        {/* Placeholder for future chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Fleet Health</h2>
          <div className="flex items-center justify-center h-64 text-gray-400">
            <div className="text-center">
              <Activity className="h-12 w-12 mx-auto mb-2" />
              <p>Health chart coming soon</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
