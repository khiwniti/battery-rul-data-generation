/**
 * WebSocket Client
 * Socket.IO client for real-time battery telemetry and alerts
 */
import { io, Socket } from 'socket.io-client'
import { useAuthStore } from '@/stores/authStore'

const WS_URL = import.meta.env.VITE_WS_URL || 'http://localhost:8000'

class WebSocketClient {
  private socket: Socket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5

  connect() {
    const token = useAuthStore.getState().token

    if (!token) {
      console.warn('Cannot connect WebSocket: No auth token')
      return
    }

    this.socket = io(WS_URL, {
      auth: {
        token,
      },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: this.maxReconnectAttempts,
    })

    this.setupEventListeners()
  }

  private setupEventListeners() {
    if (!this.socket) return

    this.socket.on('connect', () => {
      console.log('WebSocket connected:', this.socket?.id)
      this.reconnectAttempts = 0
    })

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason)
    })

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error)
      this.reconnectAttempts++

      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.error('Max reconnection attempts reached')
        this.disconnect()
      }
    })

    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error)
    })
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
  }

  // Subscribe to location-specific telemetry updates
  subscribeToLocation(locationId: string) {
    if (!this.socket) {
      console.warn('WebSocket not connected')
      return
    }

    this.socket.emit('subscribe_location', { location_id: locationId })
    console.log('Subscribed to location:', locationId)
  }

  // Unsubscribe from location
  unsubscribeFromLocation(locationId: string) {
    if (!this.socket) return

    this.socket.emit('unsubscribe_location', { location_id: locationId })
    console.log('Unsubscribed from location:', locationId)
  }

  // Subscribe to specific battery updates
  subscribeToBattery(batteryId: string) {
    if (!this.socket) {
      console.warn('WebSocket not connected')
      return
    }

    this.socket.emit('subscribe_battery', { battery_id: batteryId })
    console.log('Subscribed to battery:', batteryId)
  }

  // Unsubscribe from battery
  unsubscribeFromBattery(batteryId: string) {
    if (!this.socket) return

    this.socket.emit('unsubscribe_battery', { battery_id: batteryId })
    console.log('Unsubscribed from battery:', batteryId)
  }

  // Listen for telemetry updates
  onTelemetryUpdate(callback: (data: any) => void) {
    if (!this.socket) return

    this.socket.on('telemetry_update', callback)
  }

  // Listen for alerts
  onAlert(callback: (data: any) => void) {
    if (!this.socket) return

    this.socket.on('alert', callback)
  }

  // Listen for RUL prediction updates
  onRULUpdate(callback: (data: any) => void) {
    if (!this.socket) return

    this.socket.on('rul_update', callback)
  }

  // Remove event listeners
  off(event: string, callback?: (data: any) => void) {
    if (!this.socket) return

    if (callback) {
      this.socket.off(event, callback)
    } else {
      this.socket.off(event)
    }
  }

  // Check if connected
  isConnected(): boolean {
    return this.socket?.connected ?? false
  }
}

// Singleton instance
export const wsClient = new WebSocketClient()

export default wsClient
