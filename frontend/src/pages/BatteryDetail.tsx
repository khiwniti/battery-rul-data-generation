/**
 * Battery Detail Page
 * Detailed telemetry, trends, and RUL prediction for single battery
 */
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Activity, Thermometer, Zap, Wifi, WifiOff } from 'lucide-react'
import { api } from '@/services/api'
import BatteryHeader from '@/components/Battery/BatteryHeader'
import TelemetryChart from '@/components/Battery/TelemetryChart'
import RULCard from '@/components/Battery/RULCard'
import { useBatteryTelemetry } from '@/hooks/useBatteryTelemetry'
import { wsClient } from '@/services/websocket'

export default function BatteryDetailPage() {
  const { batteryId } = useParams<{ batteryId: string }>()

  // Real-time telemetry updates
  const { latestUpdate, updateCount } = useBatteryTelemetry(batteryId)
  const isConnected = wsClient.isConnected()

  // Fetch battery details
  const { data: battery, isLoading: batteryLoading } = useQuery({
    queryKey: ['battery', batteryId],
    queryFn: async () => {
      const response = await api.batteries.get(batteryId!)
      return response.data
    },
    enabled: !!batteryId,
  })

  // Fetch telemetry data (last 24 hours)
  const { data: telemetryData, isLoading: telemetryLoading } = useQuery({
    queryKey: ['telemetry', batteryId],
    queryFn: async () => {
      const endDate = new Date()
      const startDate = new Date(endDate.getTime() - 24 * 60 * 60 * 1000) // 24h ago

      const response = await api.batteries.getTelemetry(batteryId!, {
        start_date: startDate.toISOString(),
        end_date: endDate.toISOString(),
        limit: 500,
      })
      return response.data
    },
    enabled: !!batteryId,
  })

  // Fetch RUL prediction (if available)
  const { data: rulData } = useQuery({
    queryKey: ['rul', batteryId],
    queryFn: async () => {
      try {
        const response = await api.predictions.getBatteryRUL(batteryId!)
        return response.data
      } catch (error) {
        // RUL may not be available yet (ML model not trained)
        return null
      }
    },
    enabled: !!batteryId,
  })

  if (batteryLoading) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow p-6 animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/4"></div>
        </div>
      </div>
    )
  }

  if (!battery) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-600">Battery not found</p>
      </div>
    )
  }

  // Determine battery status based on SOH
  const soh = battery.soh_pct || 100
  const status = soh >= 90 ? 'healthy' : soh >= 80 ? 'warning' : 'critical'

  // Transform telemetry data for charts
  const voltageData = telemetryData?.map((t: any) => ({
    timestamp: t.timestamp,
    value: t.voltage_v,
  })) || []

  const temperatureData = telemetryData?.map((t: any) => ({
    timestamp: t.timestamp,
    value: t.temperature_c,
  })) || []

  const resistanceData = telemetryData?.map((t: any) => ({
    timestamp: t.timestamp,
    value: t.internal_resistance_mohm,
  })) || []

  const sohData = telemetryData?.map((t: any) => ({
    timestamp: t.timestamp,
    value: t.soh_pct || soh,
  })) || []

  // RUL card data (mock if not available)
  const rulDays = rulData?.rul_days || 365
  const rulConfidence = rulData?.confidence || 0.85
  const riskLevel = rulDays > 180 ? 'normal' : rulDays > 90 ? 'warning' : 'critical'

  return (
    <div className="space-y-6">
      {/* Battery Header */}
      <BatteryHeader
        batteryId={battery.battery_id}
        status={status}
        soh={soh}
        locationName={battery.location_name}
      />

      {/* Real-time Status Indicator */}
      <div className={`flex items-center justify-between px-4 py-3 rounded-lg border ${
        isConnected ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'
      }`}>
        <div className="flex items-center space-x-3">
          {isConnected ? (
            <>
              <Wifi className="h-5 w-5 text-green-600" />
              <div>
                <p className="text-sm font-medium text-green-900">Live Updates Active</p>
                <p className="text-xs text-green-700">
                  {updateCount > 0 ? `${updateCount} updates received` : 'Waiting for telemetry...'}
                </p>
              </div>
            </>
          ) : (
            <>
              <WifiOff className="h-5 w-5 text-gray-600" />
              <div>
                <p className="text-sm font-medium text-gray-900">Real-time Updates Unavailable</p>
                <p className="text-xs text-gray-700">Displaying historical data only</p>
              </div>
            </>
          )}
        </div>
        {latestUpdate && (
          <div className="text-right">
            <p className="text-xs text-gray-600">Latest update</p>
            <p className="text-xs font-medium text-gray-900">
              {new Date(latestUpdate.timestamp).toLocaleTimeString()}
            </p>
          </div>
        )}
      </div>

      {/* RUL Prediction Card */}
      <RULCard
        rulDays={rulDays}
        confidence={rulConfidence}
        riskLevel={riskLevel}
        loading={false}
      />

      {/* Battery Specifications Card */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Battery Specifications</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-600">System ID</p>
            <p className="font-medium text-gray-900">{battery.system_id}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">String ID</p>
            <p className="font-medium text-gray-900">{battery.string_id}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Nominal Voltage</p>
            <p className="font-medium text-gray-900">12.0V</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Rated Capacity</p>
            <p className="font-medium text-gray-900">120 Ah</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Manufacturer</p>
            <p className="font-medium text-gray-900">{battery.manufacturer || 'VRLA Battery Co.'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Model</p>
            <p className="font-medium text-gray-900">{battery.model || 'UPS-12V-120AH'}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Install Date</p>
            <p className="font-medium text-gray-900">
              {battery.install_date ? new Date(battery.install_date).toLocaleDateString() : 'N/A'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Warranty Expiry</p>
            <p className="font-medium text-gray-900">
              {battery.warranty_expiry_date ? new Date(battery.warranty_expiry_date).toLocaleDateString() : 'N/A'}
            </p>
          </div>
        </div>
      </div>

      {/* Telemetry Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <TelemetryChart
          data={voltageData}
          title="Voltage"
          dataKey="Voltage"
          color="#3b82f6"
          unit="V"
          height={300}
        />

        <TelemetryChart
          data={temperatureData}
          title="Temperature"
          dataKey="Temperature"
          color="#ef4444"
          unit="°C"
          height={300}
        />

        <TelemetryChart
          data={resistanceData}
          title="Internal Resistance"
          dataKey="Resistance"
          color="#f59e0b"
          unit="mΩ"
          height={300}
        />

        <TelemetryChart
          data={sohData}
          title="State of Health (SOH)"
          dataKey="SOH"
          color="#10b981"
          unit="%"
          height={300}
        />
      </div>

      {/* Current Metrics Card */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Current Metrics</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="flex items-start space-x-4">
            <div className="p-3 bg-blue-100 rounded-full">
              <Zap className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Latest Voltage</p>
              <p className="text-2xl font-bold text-gray-900">
                {voltageData.length > 0
                  ? `${voltageData[voltageData.length - 1].value.toFixed(2)} V`
                  : 'N/A'
                }
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-4">
            <div className="p-3 bg-red-100 rounded-full">
              <Thermometer className="h-6 w-6 text-red-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Latest Temperature</p>
              <p className="text-2xl font-bold text-gray-900">
                {temperatureData.length > 0
                  ? `${temperatureData[temperatureData.length - 1].value.toFixed(1)} °C`
                  : 'N/A'
                }
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-4">
            <div className="p-3 bg-green-100 rounded-full">
              <Activity className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">State of Health</p>
              <p className="text-2xl font-bold text-gray-900">{soh.toFixed(1)}%</p>
            </div>
          </div>
        </div>
      </div>

      {/* Notes about data availability */}
      {!telemetryData || telemetryData.length === 0 ? (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-sm text-yellow-800">
            No telemetry data available yet. Data will appear once the sensor simulator starts generating telemetry.
          </p>
        </div>
      ) : null}

      {!rulData ? (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-800">
            RUL predictions will be available after ML model training completes (2-year dataset generation in progress).
          </p>
        </div>
      ) : null}
    </div>
  )
}
