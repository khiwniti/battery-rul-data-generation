/**
 * Header Component
 * Page header with breadcrumbs and user menu
 */
import { useLocation, useNavigate } from 'react-router-dom'
import { Bell, ChevronRight, LogOut, User, Wifi, WifiOff } from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'
import { useState, useEffect } from 'react'
import { wsClient } from '@/services/websocket'

export default function Header() {
  const location = useLocation()
  const navigate = useNavigate()
  const logout = useAuthStore((state) => state.logout)
  const [isConnected, setIsConnected] = useState(false)
  const [showUserMenu, setShowUserMenu] = useState(false)

  // Generate breadcrumbs from current path
  const generateBreadcrumbs = () => {
    const paths = location.pathname.split('/').filter(Boolean)

    if (paths.length === 0) {
      return [{ name: 'Dashboard', href: '/' }]
    }

    const breadcrumbs = [{ name: 'Dashboard', href: '/' }]

    paths.forEach((path, index) => {
      const href = '/' + paths.slice(0, index + 1).join('/')
      let name = path.charAt(0).toUpperCase() + path.slice(1)

      // Handle specific routes
      if (path.startsWith('location') && paths[index + 1]) {
        name = 'Location'
      } else if (path.startsWith('battery') && paths[index + 1]) {
        name = 'Battery'
      } else if (path.match(/^[A-Z0-9-]+$/)) {
        name = path // Keep IDs as-is
      }

      breadcrumbs.push({ name, href })
    })

    return breadcrumbs
  }

  const breadcrumbs = generateBreadcrumbs()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  // Check WebSocket connection status
  useEffect(() => {
    const interval = setInterval(() => {
      setIsConnected(wsClient.isConnected())
    }, 2000)
    return () => clearInterval(interval)
  }, [])

  return (
    <header className="bg-white shadow-sm z-10">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Breadcrumbs */}
          <div className="flex items-center space-x-2">
            {breadcrumbs.map((crumb, index) => (
              <div key={crumb.href} className="flex items-center">
                {index > 0 && (
                  <ChevronRight className="h-4 w-4 text-gray-400 mx-2" />
                )}
                {index === breadcrumbs.length - 1 ? (
                  <span className="text-sm font-medium text-gray-900">
                    {crumb.name}
                  </span>
                ) : (
                  <button
                    onClick={() => navigate(crumb.href)}
                    className="text-sm font-medium text-gray-500 hover:text-gray-900"
                  >
                    {crumb.name}
                  </button>
                )}
              </div>
            ))}
          </div>

          {/* Right side actions */}
          <div className="flex items-center space-x-4">
            {/* WebSocket Status */}
            <div className="flex items-center space-x-2">
              {isConnected ? (
                <>
                  <Wifi className="h-4 w-4 text-green-500" />
                  <span className="text-xs text-gray-600">Connected</span>
                </>
              ) : (
                <>
                  <WifiOff className="h-4 w-4 text-red-500" />
                  <span className="text-xs text-gray-600">Disconnected</span>
                </>
              )}
            </div>

            {/* Notifications */}
            <button className="relative p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100">
              <Bell className="h-5 w-5" />
              <span className="absolute top-1 right-1 block h-2 w-2 rounded-full bg-red-500 ring-2 ring-white" />
            </button>

            {/* User Menu */}
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100"
              >
                <div className="h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center">
                  <User className="h-5 w-5 text-white" />
                </div>
              </button>

              {/* Dropdown menu */}
              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-10 border border-gray-200">
                  <button
                    onClick={handleLogout}
                    className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    <LogOut className="h-4 w-4 mr-2" />
                    Logout
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
