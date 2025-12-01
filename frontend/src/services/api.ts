/**
 * API Client
 * Axios-based HTTP client with JWT token interceptors
 */
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/stores/authStore'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - Add JWT token to requests
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = useAuthStore.getState().token

    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

// Response interceptor - Handle errors globally
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean
    }

    // Handle 401 Unauthorized - Token expired
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      // Try to refresh token
      try {
        const refreshToken = useAuthStore.getState().refreshToken

        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          })

          const { access_token } = response.data

          // Update token in store
          useAuthStore.getState().setToken(access_token)

          // Retry original request with new token
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`
          }

          return apiClient(originalRequest)
        }
      } catch (refreshError) {
        // Refresh failed - Logout user
        useAuthStore.getState().logout()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    // Handle other errors
    return Promise.reject(error)
  }
)

// API methods
export const api = {
  // Auth
  auth: {
    login: (username: string, password: string) =>
      apiClient.post('/api/v1/auth/login', { username, password }),

    logout: () => apiClient.post('/api/v1/auth/logout'),

    refresh: (refreshToken: string) =>
      apiClient.post('/api/v1/auth/refresh', { refresh_token: refreshToken }),
  },

  // Locations
  locations: {
    list: () => apiClient.get('/api/v1/locations'),
    get: (locationId: string) => apiClient.get(`/api/v1/locations/${locationId}`),
  },

  // Batteries
  batteries: {
    list: (locationId?: string) =>
      apiClient.get('/api/v1/batteries', { params: { location_id: locationId } }),

    get: (batteryId: string) => apiClient.get(`/api/v1/batteries/${batteryId}`),

    telemetry: (batteryId: string, params?: { start?: string; end?: string }) =>
      apiClient.get(`/api/v1/batteries/${batteryId}/telemetry`, { params }),
  },

  // Alerts
  alerts: {
    list: (params?: { location_id?: string; severity?: string; active?: boolean }) =>
      apiClient.get('/api/v1/alerts', { params }),

    acknowledge: (alertId: string) =>
      apiClient.post(`/api/v1/alerts/${alertId}/acknowledge`),
  },

  // RUL Predictions
  predictions: {
    get: (batteryId: string) =>
      apiClient.get(`/api/v1/predictions/${batteryId}`),

    batch: (locationId: string) =>
      apiClient.get('/api/v1/predictions/batch', { params: { location_id: locationId } }),
  },
}

export default apiClient
