/**
 * Sidebar Navigation Component
 * Main navigation menu with icons
 */
import { Link, useLocation } from 'react-router-dom'
import { Home, MapPin, Battery, AlertTriangle, Users, BarChart3, Zap } from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'

interface NavItem {
  name: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  roles?: string[] // If specified, only show for these roles
}

const navigation: NavItem[] = [
  { name: 'Dashboard', href: '/', icon: Home },
  { name: 'Locations', href: '/locations', icon: MapPin },
  { name: 'Batteries', href: '/batteries', icon: Battery },
  { name: 'Alerts', href: '/alerts', icon: AlertTriangle },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'Simulator', href: '/simulator', icon: Zap, roles: ['engineer', 'admin'] },
  { name: 'Users', href: '/users', icon: Users, roles: ['admin'] },
]

export default function Sidebar() {
  const location = useLocation()
  const user = useAuthStore((state) => state.user)

  const filteredNavigation = navigation.filter(item => {
    if (!item.roles) return true
    return item.roles.includes(user?.role || '')
  })

  return (
    <div className="hidden md:flex md:w-64 md:flex-col">
      <div className="flex flex-col flex-grow bg-gray-900 overflow-y-auto">
        {/* Logo */}
        <div className="flex items-center flex-shrink-0 px-4 py-5">
          <Battery className="h-8 w-8 text-blue-500" />
          <span className="ml-2 text-xl font-bold text-white">
            Battery RUL
          </span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-2 py-4 space-y-1">
          {filteredNavigation.map((item) => {
            const isActive = location.pathname === item.href
            const Icon = item.icon

            return (
              <Link
                key={item.name}
                to={item.href}
                className={`
                  group flex items-center px-3 py-2 text-sm font-medium rounded-md
                  transition-colors duration-150
                  ${isActive
                    ? 'bg-gray-800 text-white'
                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                  }
                `}
              >
                <Icon
                  className={`
                    mr-3 h-5 w-5
                    ${isActive ? 'text-blue-500' : 'text-gray-400 group-hover:text-gray-300'}
                  `}
                />
                {item.name}
              </Link>
            )
          })}
        </nav>

        {/* User info */}
        <div className="flex-shrink-0 flex border-t border-gray-800 p-4">
          <div className="flex items-center w-full">
            <div className="flex-shrink-0">
              <div className="h-10 w-10 rounded-full bg-gray-700 flex items-center justify-center">
                <span className="text-sm font-medium text-white">
                  {user?.username?.charAt(0).toUpperCase() || 'U'}
                </span>
              </div>
            </div>
            <div className="ml-3 flex-1">
              <p className="text-sm font-medium text-white">
                {user?.username || 'User'}
              </p>
              <p className="text-xs text-gray-400 capitalize">
                {user?.role || 'viewer'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
