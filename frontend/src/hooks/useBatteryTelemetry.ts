/**
 * useBatteryTelemetry Hook
 * Real-time battery telemetry updates via WebSocket
 */
import { useEffect, useState, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { wsClient } from '@/services/websocket'

interface TelemetryUpdate {
  battery_id: string
  data: {
    voltage_v: number
    temperature_c: number
    internal_resistance_mohm: number
    soh_pct?: number
    timestamp: string
  }
  timestamp: string
}

export function useBatteryTelemetry(batteryId: string | undefined) {
  const queryClient = useQueryClient()
  const [latestUpdate, setLatestUpdate] = useState<TelemetryUpdate | null>(null)
  const [updateCount, setUpdateCount] = useState(0)

  const handleTelemetryUpdate = useCallback(
    (data: TelemetryUpdate) => {
      if (data.battery_id === batteryId) {
        setLatestUpdate(data)
        setUpdateCount((prev) => prev + 1)

        // Update query cache with new data point
        queryClient.setQueryData(['telemetry', batteryId], (oldData: any) => {
          if (!oldData) return oldData

          // Add new data point to the end of the array
          return [...oldData, {
            timestamp: data.data.timestamp,
            voltage_v: data.data.voltage_v,
            temperature_c: data.data.temperature_c,
            internal_resistance_mohm: data.data.internal_resistance_mohm,
            soh_pct: data.data.soh_pct,
          }]
        })
      }
    },
    [batteryId, queryClient]
  )

  useEffect(() => {
    if (!batteryId) return

    // Subscribe to battery updates
    wsClient.subscribeToBattery(batteryId)

    // Listen for telemetry updates
    wsClient.onTelemetryUpdate(handleTelemetryUpdate)

    // Cleanup
    return () => {
      wsClient.unsubscribeFromBattery(batteryId)
      wsClient.off('telemetry_update', handleTelemetryUpdate)
    }
  }, [batteryId, handleTelemetryUpdate])

  return {
    latestUpdate,
    updateCount,
    isSubscribed: !!batteryId,
  }
}

export default useBatteryTelemetry
