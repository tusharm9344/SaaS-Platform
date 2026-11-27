import { useCallback, useEffect, useState } from 'react'
import {
  Container,
  Activity,
  Cpu,
  MemoryStick,
  RefreshCw,
  Search,
} from 'lucide-react'

import Sidebar from '../components/layout/Sidebar'
import Navbar from '../components/layout/Navbar'
import { getContainers } from '../services/containerService'

function formatMemory(value) {
  if (value === null || value === undefined) return '—'
  return `${Number(value).toFixed(1)} MB`
}

function StatusBadge({ status }) {
  const running = status?.toLowerCase() === 'running'

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${
        running
          ? 'bg-green-50 text-green-700'
          : 'bg-gray-100 text-gray-600'
      }`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${
          running ? 'bg-green-500' : 'bg-gray-400'
        }`}
      />
      {status || 'Unknown'}
    </span>
  )
}

function MetricBar({ value }) {
  if (value === null || value === undefined) {
    return <span className="text-[#86868b]">—</span>
  }

  const percentage = Math.min(Math.max(Number(value), 0), 100)

  return (
    <div className="flex min-w-24 items-center gap-2">
      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-[#e5e5ea]">
        <div
          className="h-full rounded-full bg-[#0071e3]"
          style={{ width: `${percentage}%` }}
        />
      </div>

      <span className="text-xs text-[#6e6e73]">
        {Number(value).toFixed(1)}%
      </span>
    </div>
  )
}

function Containers() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [containers, setContainers] = useState([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [lastUpdated, setLastUpdated] = useState(null)

  const fetchContainers = useCallback(async (manual = false) => {
    try {
      if (manual) {
        setRefreshing(true)
      }

      const data = await getContainers()

      setContainers(data.containers || [])
      setLastUpdated(new Date())
      setError('')
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to fetch container information.'
      )
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    fetchContainers()

    const interval = setInterval(() => {
      fetchContainers()
    }, 30000)

    return () => clearInterval(interval)
  }, [fetchContainers])

  const runningCount = containers.filter(
    (container) => container.status?.toLowerCase() === 'running'
  ).length

  const stoppedCount = containers.length - runningCount

  const filteredContainers = containers.filter((container) => {
    const query = search.toLowerCase()

    return (
      container.name?.toLowerCase().includes(query) ||
      container.image?.toLowerCase().includes(query) ||
      container.service_name?.toLowerCase().includes(query)
    )
  })

  const averageCpu = containers
    .filter(
      (container) =>
        container.status?.toLowerCase() === 'running' &&
        container.cpu_percent !== null &&
        container.cpu_percent !== undefined
    )

  const cpuAverage = averageCpu.length
    ? averageCpu.reduce(
        (total, container) => total + Number(container.cpu_percent),
        0
      ) / averageCpu.length
    : null

  const stats = [
    {
      title: 'Total Containers',
      value: containers.length,
      icon: Container,
      color: 'text-[#0071e3]',
      bg: 'bg-blue-50',
    },
    {
      title: 'Running',
      value: runningCount,
      icon: Activity,
      color: 'text-green-600',
      bg: 'bg-green-50',
    },
    {
      title: 'Stopped',
      value: stoppedCount,
      icon: Container,
      color: 'text-gray-600',
      bg: 'bg-gray-100',
    },
    {
      title: 'Average CPU',
      value: cpuAverage === null ? '—' : `${cpuAverage.toFixed(2)}%`,
      icon: Cpu,
      color: 'text-purple-600',
      bg: 'bg-purple-50',
    },
  ]

  return (
    <div className="min-h-screen bg-[#f5f5f7]">
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <main className="min-h-screen">
        <Navbar onMenuClick={() => setSidebarOpen(true)} />

        <div className="page-container px-6 py-8">

          {/* Header */}
          <div className="mb-8 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
            <div>
              <h1 className="text-2xl font-semibold tracking-tight text-[#1d1d1f]">
                Containers
              </h1>

              <p className="mt-1 text-sm text-[#86868b]">
                Monitor CPU and memory utilization across your containers.
              </p>
            </div>

            <button
              onClick={() => fetchContainers(true)}
              disabled={refreshing}
              className="flex items-center justify-center gap-2 rounded-lg border border-[#d2d2d7] bg-white px-4 py-2 text-sm font-medium text-[#1d1d1f] transition hover:bg-[#f5f5f7] disabled:opacity-50"
            >
              <RefreshCw
                size={15}
                className={refreshing ? 'animate-spin' : ''}
              />
              Refresh
            </button>
          </div>

          {/* Statistics */}
          <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {stats.map((stat) => {
              const Icon = stat.icon

              return (
                <div
                  key={stat.title}
                  className="rounded-2xl border border-[#e5e5ea] bg-white p-5"
                >
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-[#86868b]">
                      {stat.title}
                    </p>

                    <div className={`rounded-lg p-2 ${stat.bg}`}>
                      <Icon size={18} className={stat.color} />
                    </div>
                  </div>

                  <p className="mt-4 text-2xl font-semibold text-[#1d1d1f]">
                    {stat.value}
                  </p>
                </div>
              )
            })}
          </div>

          {/* Container table */}
          <div className="overflow-hidden rounded-2xl border border-[#e5e5ea] bg-white">

            <div className="flex flex-col justify-between gap-4 border-b border-[#e5e5ea] p-5 sm:flex-row sm:items-center">
              <div>
                <h2 className="font-semibold text-[#1d1d1f]">
                  Container Inventory
                </h2>

                <p className="mt-1 text-xs text-[#86868b]">
                  Live resource utilization · Refreshes every 30 seconds
                </p>
              </div>

              <div className="relative">
                <Search
                  size={16}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-[#86868b]"
                />

                <input
                  type="text"
                  placeholder="Search containers..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full rounded-lg border border-[#e5e5ea] bg-[#fafafa] py-2 pl-9 pr-3 text-sm outline-none focus:border-[#0071e3] sm:w-64"
                />
              </div>
            </div>

            {error && (
              <div className="m-5 rounded-lg bg-red-50 p-3 text-sm text-red-600">
                {error}
              </div>
            )}

            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-[#fafafa]">
                  <tr className="border-b border-[#e5e5ea] text-xs font-medium uppercase tracking-wide text-[#86868b]">
                    <th className="px-5 py-4">Container</th>
                    <th className="px-5 py-4">Image</th>
                    <th className="px-5 py-4">Service</th>
                    <th className="px-5 py-4">Status</th>
                    <th className="px-5 py-4">CPU</th>
                    <th className="px-5 py-4">Memory</th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-[#f0f0f2]">
                  {loading ? (
                    <tr>
                      <td
                        colSpan="6"
                        className="px-5 py-12 text-center text-sm text-[#86868b]"
                      >
                        Loading containers...
                      </td>
                    </tr>
                  ) : filteredContainers.length === 0 ? (
                    <tr>
                      <td
                        colSpan="6"
                        className="px-5 py-12 text-center text-sm text-[#86868b]"
                      >
                        No containers found.
                      </td>
                    </tr>
                  ) : (
                    filteredContainers.map((container) => (
                      <tr
                        key={container.id}
                        className="transition hover:bg-[#fafafa]"
                      >
                        <td className="px-5 py-4">
                          <p className="text-sm font-medium text-[#1d1d1f]">
                            {container.name || 'Unnamed container'}
                          </p>

                          <p className="mt-1 text-xs text-[#86868b]">
                            {container.container_id?.slice(0, 12) || '—'}
                          </p>
                        </td>

                        <td className="max-w-48 truncate px-5 py-4 text-sm text-[#6e6e73]">
                          {container.image || '—'}
                        </td>

                        <td className="px-5 py-4 text-sm text-[#6e6e73]">
                          {container.service_name || '—'}
                        </td>

                        <td className="px-5 py-4">
                          <StatusBadge status={container.status} />
                        </td>

                        <td className="px-5 py-4">
                          <MetricBar value={container.cpu_percent} />
                        </td>

                        <td className="px-5 py-4">
                          <div className="min-w-32">
                            <p className="text-sm font-medium text-[#1d1d1f]">
                              {formatMemory(container.memory_usage_mb)}
                            </p>

                            <div className="mt-1">
                              <MetricBar value={container.memory_percent} />
                            </div>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Footer */}
            <div className="flex flex-col justify-between gap-2 border-t border-[#e5e5ea] px-5 py-4 text-xs text-[#86868b] sm:flex-row">
              <span>
                Showing {filteredContainers.length} of {containers.length} containers
              </span>

              <span>
                Last updated:{' '}
                {lastUpdated
                  ? lastUpdated.toLocaleTimeString()
                  : '—'}
              </span>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default Containers
