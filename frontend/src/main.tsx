/**
 * Main Application Entry Point
 * React 18 with React Router, TanStack Query, and authentication
 */
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuthStore } from '@/stores/authStore'
import './index.css'

// Lazy load pages
const LoginPage = React.lazy(() => import('@/pages/Login'))
const DashboardPage = React.lazy(() => import('@/pages/Dashboard'))
const LocationPage = React.lazy(() => import('@/pages/Location'))
const BatteryDetailPage = React.lazy(() => import('@/pages/BatteryDetail'))
const SimulatorControlPanelPage = React.lazy(() => import('@/pages/SimulatorControlPanel'))
const AlertsPage = React.lazy(() => import('@/pages/Alerts'))

// Import Layout
import MainLayout from '@/components/Layout/MainLayout'

// Create Query Client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30000, // 30 seconds
    },
  },
})

// Protected Route Component with Layout
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <MainLayout>{children}</MainLayout>
}

// App Component
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <React.Suspense
          fallback={
            <div className="flex items-center justify-center h-screen">
              <div className="text-lg">Loading...</div>
            </div>
          }
        >
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginPage />} />

            {/* Protected routes */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/location/:locationId"
              element={
                <ProtectedRoute>
                  <LocationPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/battery/:batteryId"
              element={
                <ProtectedRoute>
                  <BatteryDetailPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/simulator"
              element={
                <ProtectedRoute>
                  <SimulatorControlPanelPage />
                </ProtectedRoute>
              }
            />

            <Route
              path="/alerts"
              element={
                <ProtectedRoute>
                  <AlertsPage />
                </ProtectedRoute>
              }
            />

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </React.Suspense>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

// Render app
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
