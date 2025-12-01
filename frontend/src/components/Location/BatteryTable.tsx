/**
 * Battery Table Component
 * Displays sortable, filterable table of batteries at a location
 */
import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Battery, TrendingDown, AlertTriangle, Search } from 'lucide-react'

interface BatteryData {
  battery_id: string
  string_id: string
  system_id: string
  soh_pct: number
  voltage_v?: number
  temperature_c?: number
  internal_resistance_mohm?: number
  alert_count?: number
  last_update?: string
}

interface BatteryTableProps {
  batteries: BatteryData[]
  loading?: boolean
}

type SortKey = 'battery_id' | 'soh_pct' | 'voltage_v' | 'temperature_c' | 'alert_count'
type SortOrder = 'asc' | 'desc'

export default function BatteryTable({ batteries, loading }: BatteryTableProps) {
  const navigate = useNavigate()
  const [searchTerm, setSearchTerm] = useState('')
  const [sortKey, setSortKey] = useState<SortKey>('battery_id')
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc')
  const [filterStatus, setFilterStatus] = useState<'all' | 'healthy' | 'warning' | 'critical'>('all')

  // Filter and sort batteries
  const filteredBatteries = useMemo(() => {
    let filtered = batteries

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(b =>
        b.battery_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        b.string_id.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    // Apply status filter
    if (filterStatus !== 'all') {
      filtered = filtered.filter(b => {
        const soh = b.soh_pct || 100
        if (filterStatus === 'healthy') return soh >= 90
        if (filterStatus === 'warning') return soh >= 80 && soh < 90
        if (filterStatus === 'critical') return soh < 80
        return true
      })
    }

    // Apply sorting
    const sorted = [...filtered].sort((a, b) => {
      let aVal = a[sortKey]
      let bVal = b[sortKey]

      // Handle undefined values
      if (aVal === undefined) aVal = 0
      if (bVal === undefined) bVal = 0

      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sortOrder === 'asc'
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal)
      }

      return sortOrder === 'asc'
        ? Number(aVal) - Number(bVal)
        : Number(bVal) - Number(aVal)
    })

    return sorted
  }, [batteries, searchTerm, sortKey, sortOrder, filterStatus])

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortOrder('asc')
    }
  }

  const getStatusBadge = (soh: number) => {
    if (soh >= 90) {
      return <span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">Healthy</span>
    } else if (soh >= 80) {
      return <span className="px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800">Warning</span>
    } else {
      return <span className="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800">Critical</span>
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-6 animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      {/* Filters and search */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
          {/* Search */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search batteries..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Status filter */}
          <div className="flex space-x-2">
            <button
              onClick={() => setFilterStatus('all')}
              className={`px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                filterStatus === 'all'
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              All ({batteries.length})
            </button>
            <button
              onClick={() => setFilterStatus('healthy')}
              className={`px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                filterStatus === 'healthy'
                  ? 'bg-green-100 text-green-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Healthy
            </button>
            <button
              onClick={() => setFilterStatus('warning')}
              className={`px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                filterStatus === 'warning'
                  ? 'bg-yellow-100 text-yellow-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Warning
            </button>
            <button
              onClick={() => setFilterStatus('critical')}
              className={`px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                filterStatus === 'critical'
                  ? 'bg-red-100 text-red-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Critical
            </button>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left">
                <button
                  onClick={() => handleSort('battery_id')}
                  className="flex items-center space-x-1 text-xs font-medium text-gray-700 uppercase tracking-wider hover:text-gray-900"
                >
                  <span>Battery ID</span>
                  {sortKey === 'battery_id' && (
                    <span>{sortOrder === 'asc' ? '↑' : '↓'}</span>
                  )}
                </button>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                String
              </th>
              <th className="px-6 py-3 text-left">
                <button
                  onClick={() => handleSort('soh_pct')}
                  className="flex items-center space-x-1 text-xs font-medium text-gray-700 uppercase tracking-wider hover:text-gray-900"
                >
                  <span>SOH</span>
                  {sortKey === 'soh_pct' && (
                    <span>{sortOrder === 'asc' ? '↑' : '↓'}</span>
                  )}
                </button>
              </th>
              <th className="px-6 py-3 text-left">
                <button
                  onClick={() => handleSort('voltage_v')}
                  className="flex items-center space-x-1 text-xs font-medium text-gray-700 uppercase tracking-wider hover:text-gray-900"
                >
                  <span>Voltage</span>
                  {sortKey === 'voltage_v' && (
                    <span>{sortOrder === 'asc' ? '↑' : '↓'}</span>
                  )}
                </button>
              </th>
              <th className="px-6 py-3 text-left">
                <button
                  onClick={() => handleSort('temperature_c')}
                  className="flex items-center space-x-1 text-xs font-medium text-gray-700 uppercase tracking-wider hover:text-gray-900"
                >
                  <span>Temp</span>
                  {sortKey === 'temperature_c' && (
                    <span>{sortOrder === 'asc' ? '↑' : '↓'}</span>
                  )}
                </button>
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left">
                <button
                  onClick={() => handleSort('alert_count')}
                  className="flex items-center space-x-1 text-xs font-medium text-gray-700 uppercase tracking-wider hover:text-gray-900"
                >
                  <span>Alerts</span>
                  {sortKey === 'alert_count' && (
                    <span>{sortOrder === 'asc' ? '↑' : '↓'}</span>
                  )}
                </button>
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredBatteries.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-12 text-center">
                  <Battery className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-600">No batteries found</p>
                </td>
              </tr>
            ) : (
              filteredBatteries.map((battery) => (
                <tr
                  key={battery.battery_id}
                  onClick={() => navigate(`/battery/${battery.battery_id}`)}
                  className="hover:bg-gray-50 cursor-pointer transition-colors"
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <Battery className="h-4 w-4 text-gray-400 mr-2" />
                      <span className="text-sm font-medium text-gray-900">
                        {battery.battery_id}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {battery.string_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <span className="text-sm font-medium text-gray-900">
                        {(battery.soh_pct || 100).toFixed(1)}%
                      </span>
                      {battery.soh_pct < 90 && (
                        <TrendingDown className="h-4 w-4 text-red-500 ml-2" />
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {battery.voltage_v ? `${battery.voltage_v.toFixed(2)} V` : 'N/A'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {battery.temperature_c ? `${battery.temperature_c.toFixed(1)} °C` : 'N/A'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {getStatusBadge(battery.soh_pct || 100)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {battery.alert_count && battery.alert_count > 0 ? (
                      <div className="flex items-center text-red-600">
                        <AlertTriangle className="h-4 w-4 mr-1" />
                        <span className="text-sm font-medium">{battery.alert_count}</span>
                      </div>
                    ) : (
                      <span className="text-sm text-gray-400">-</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Footer with count */}
      <div className="px-6 py-3 bg-gray-50 border-t border-gray-200">
        <p className="text-sm text-gray-600">
          Showing {filteredBatteries.length} of {batteries.length} batteries
        </p>
      </div>
    </div>
  )
}
