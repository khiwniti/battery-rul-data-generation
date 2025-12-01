/**
 * useWebSocket Hook
 * Custom React hook for WebSocket connection management
 */
import { useEffect, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { wsClient } from '@/services/websocket'
import { useAuthStore } from '@/stores/authStore'

export function useWebSocket() {
  const queryClient = useQueryClient()
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const isConnectedRef = useRef(false)

  useEffect(() => {
    if (isAuthenticated && !isConnectedRef.current) {
      // Connect WebSocket
      wsClient.connect()
      isConnectedRef.current = true

      // Setup global alert listener
      wsClient.onAlert((data) => {
        console.log('New alert received:', data)

        // Invalidate alerts query to refresh
        queryClient.invalidateQueries({ queryKey: ['alerts'] })
        queryClient.invalidateQueries({ queryKey: ['alerts-recent'] })

        // TODO: Add toast notification
      })

      // Cleanup on unmount
      return () => {
        wsClient.disconnect()
        isConnectedRef.current = false
      }
    }
  }, [isAuthenticated, queryClient])

  return {
    isConnected: wsClient.isConnected(),
    subscribe: {
      location: (locationId: string) => wsClient.subscribeToLocation(locationId),
      battery: (batteryId: string) => wsClient.subscribeToBattery(batteryId),
    },
    unsubscribe: {
      location: (locationId: string) => wsClient.unsubscribeFromLocation(locationId),
      battery: (batteryId: string) => wsClient.unsubscribeFromBattery(batteryId),
    },
  }
}

export default useWebSocket
