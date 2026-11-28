import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AlertTriangle,
  Activity,
  CheckCircle,
  Bug,
  Clock,
  Container,
  Cpu,
  MemoryStick,
  RefreshCw,
  Server,
} from 'lucide-react'

import Sidebar from '../components/layout/Sidebar'
import Navbar from '../components/layout/Navbar'
import StatisticsCard from '../components/ui/StatisticsCard'

import {
  getIncidents,
  resolveIncident as resolveIncidentAPI,
} from '../services/incidentService'
import { getContainers } from '../services/containerService'

function formatRelativeTime(value) {
  if (!value) return 'Unknown'

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Unknown'

  const seconds = Math.floor((Date.now() - date.getTime()) / 1000)

  if (seconds < 60) return 'Just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`

  return date.toLocaleDateString()
}

function formatStatus(status) {
  if (!status) return 'Unknown'
  return status.charAt(0).toUpperCase() + status.slice(1).toLowerCase()
}

function Dashboard() {
  const navigate = useNavigate()

  const [incidents, setIncidents] = useState([])
  const [containers, setContainers] = useState([])

  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')
  const [incidentError, setIncidentError] = useState('')
  const [containerError, setContainerError] = useState('')

  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [resolvingId, setResolvingId] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)

  const fetchDashboard = useCallback(async (manual = false) => {
    if (manual) setRefreshing(true)

    setError('')
    setIncidentError('')
    setContainerError('')

    const [incidentResult, containerResult] = await Promise.allSettled([
      getIncidents(),
      getContainers(),
    ])

    if (incidentResult.status === 'fulfilled') {
      const data = incidentResult.value
      setIncidents(data.results || [])
    } else {
      setIncidentError(
        incidentResult.reason?.response?.data?.detail ||
        'Unable to load incidents.'
      )
    }

    if (containerResult.status === 'fulfilled') {
      const data = containerResult.value
      setContainers(data.containers || [])
    } else {
      setContainerError(
        containerResult.reason?.response?.data?.detail ||
        'Unable to load container information.'
      )
    }

    if (
      incidentResult.status === 'fulfilled' ||
      containerResult.status === 'fulfilled'
    ) {
      setLastUpdated(new Date())
    }

    if (
      incidentResult.status === 'rejected' &&
      containerResult.status === 'rejected'
    ) {
      setError('Unable to connect to RuntimeRCA. Check your API connection.')
    }

    setLoading(false)
    setRefreshing(false)
  }, [])

  useEffect(() => {
    fetchDashboard()

    const interval = setInterval(() => {
      fetchDashboard()
    }, 30000)

    return () => clearInterval(interval)
  }, [fetchDashboard])

  const statistics = useMemo(() => ({
    total: incidents.length,
    open: incidents.filter((item) => item.status === 'open').length,
    investigating: incidents.filter(
      (item) => item.status === 'investigating'
    ).length,
    resolved: incidents.filter((item) => item.status === 'resolved').length,
    ignored: incidents.filter((item) => item.status === 'ignored').length,
  }), [incidents])

  const infrastructure = useMemo(() => {
    const running = containers.filter(
      (item) => item.status?.toLowerCase() === 'running'
    )

    const stopped = containers.length - running.length

    const cpuValues = running
      .filter((item) => item.cpu_percent != null)
      .map((item) => Number(item.cpu_percent))
      .filter(Number.isFinite)

    const memoryValues = running
      .filter((item) => item.memory_percent != null)
      .map((item) => Number(item.memory_percent))
      .filter(Number.isFinite)

    const average = (values) =>
      values.length
        ? values.reduce((sum, value) => sum + value, 0) / values.length
        : null

    return {
      total: containers.length,
      running: running.length,
      stopped,
      cpu: average(cpuValues),
      memory: average(memoryValues),
    }
  }, [containers])

  const filteredIncidents = incidents.filter((incident) => {
    const query = searchQuery.toLowerCase()

    const matchesSearch =
      incident.title?.toLowerCase().includes(query) ||
      incident.service_name?.toLowerCase().includes(query) ||
      incident.environment?.toLowerCase().includes(query)

    const matchesStatus =
      statusFilter === 'all' || incident.status === statusFilter

    return matchesSearch && matchesStatus
  })

  const handleResolveIncident = async (incidentId) => {
    try {
      setResolvingId(incidentId)
      await resolveIncidentAPI(incidentId)
      await fetchDashboard()
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to resolve incident. Please try again.'
      )
    } finally {
      setResolvingId(null)
    }
  }

  const today = new Date().toLocaleDateString('en-IN', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  })

  return (
    <div className="min-h-screen bg-[#f5f5f7]">
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <main className="min-h-screen">
        <Navbar onMenuClick={() => setSidebarOpen(true)} />

        <div className="page-container">

          <section className="page-section flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
            <div>
              <p className="mb-2 text-sm font-medium text-[#86868b]">
                {today}
              </p>

              <h1 className="text-[32px] font-semibold tracking-[-0.04em] text-[#1d1d1f]">
                Overview
              </h1>

              <p className="mt-2 max-w-xl text-[15px] leading-6 text-[#86868b]">
                Monitor application errors, infrastructure health and automated investigations.
              </p>
            </div>

            <button
              onClick={() => fetchDashboard(true)}
              disabled={refreshing}
              className="flex items-center gap-2 rounded-lg bg-[#0071e3] px-4 py-2.5 text-sm font-medium text-white transition hover:bg-[#0077ed] disabled:opacity-50"
            >
              <RefreshCw
                size={16}
                className={refreshing ? 'animate-spin' : ''}
              />
              Refresh dashboard
            </button>
          </section>

          {error && (
            <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
              {error}
            </div>
          )}

          {/* Incident statistics */}
          <section className="mb-8">
            <div className="mb-4 flex items-center gap-2">
              <Bug size={17} className="text-[#0071e3]" />
              <h2 className="text-sm font-semibold text-[#1d1d1f]">
                Incident overview
              </h2>
            </div>

            {incidentError && (
              <p className="mb-3 text-sm text-red-600">{incidentError}</p>
            )}

            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-4">
              <StatisticsCard
                title="Total Incidents"
                value={loading ? '—' : statistics.total}
                icon={Bug}
                color="bg-[#e8f1fc] text-[#0071e3]"
                description="Recorded incidents"
              />

              <StatisticsCard
                title="Open Incidents"
                value={loading ? '—' : statistics.open}
                icon={AlertTriangle}
                color="bg-[#fff0e5] text-[#ff9500]"
                description="Require attention"
              />

              <StatisticsCard
                title="Investigating"
                value={loading ? '—' : statistics.investigating}
                icon={Activity}
                color="bg-[#e8f1fc] text-[#0071e3]"
                description="Under RCA analysis"
              />

              <StatisticsCard
                title="Resolved"
                value={loading ? '—' : statistics.resolved}
                icon={CheckCircle}
                color="bg-[#e8f8ed] text-[#34a853]"
                description="Successfully resolved"
              />
            </div>
          </section>

          {/* Infrastructure statistics */}
          <section className="mb-8">
            <div className="mb-4 flex items-center gap-2">
              <Server size={17} className="text-[#0071e3]" />
              <h2 className="text-sm font-semibold text-[#1d1d1f]">
                Infrastructure overview
              </h2>
            </div>

            {containerError && (
              <p className="mb-3 text-sm text-red-600">{containerError}</p>
            )}

            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-4">
              <StatisticsCard
                title="Total Containers"
                value={loading && !containers.length ? '—' : infrastructure.total}
                icon={Container}
                color="bg-[#e8f1fc] text-[#0071e3]"
                description="Discovered containers"
              />

              <StatisticsCard
                title="Running"
                value={loading && !containers.length ? '—' : infrastructure.running}
                icon={Activity}
                color="bg-[#e8f8ed] text-[#34a853]"
                description={`${infrastructure.stopped} stopped or inactive`}
              />

              <StatisticsCard
                title="Average CPU"
                value={infrastructure.cpu == null ? '—' : `${infrastructure.cpu.toFixed(1)}%`}
                icon={Cpu}
                color="bg-[#f0eafa] text-[#8e5ce6]"
                description="Across running containers with metrics"
              />

              <StatisticsCard
                title="Average Memory"
                value={infrastructure.memory == null ? '—' : `${infrastructure.memory.toFixed(1)}%`}
                icon={MemoryStick}
                color="bg-[#fff0e5] text-[#ff9500]"
                description="Across running containers with metrics"
              />
            </div>
          </section>

          {/* Main dashboard */}
          <section className="grid grid-cols-1 items-start gap-6 xl:grid-cols-12">

            {/* Recent incidents */}
            <div className="settings-panel min-w-0 overflow-hidden xl:col-span-8">
              <div className="flex items-center justify-between gap-4 border-b border-[#e5e5ea] px-6 py-5">
                <div>
                  <h2 className="text-base font-semibold text-[#1d1d1f]">
                    Recent incidents
                  </h2>
                  <p className="mt-1 text-xs text-[#86868b]">
                    Review and manage application errors.
                  </p>
                </div>

                <button
                  onClick={() => navigate('/incidents')}
                  className="text-sm font-medium text-[#0071e3] hover:underline"
                >
                  View all
                </button>
              </div>

              <div className="flex flex-col gap-3 px-6 py-4 sm:flex-row">
                <input
                  type="text"
                  placeholder="Search incidents or services..."
                  value={searchQuery}
                  onChange={(event) => setSearchQuery(event.target.value)}
                  className="min-h-10 flex-1 rounded-lg border border-[#e5e5ea] bg-white px-4 text-sm outline-none focus:border-[#0071e3]"
                />

                <select
                  value={statusFilter}
                  onChange={(event) => setStatusFilter(event.target.value)}
                  className="min-h-10 rounded-lg border border-[#e5e5ea] bg-white px-4 text-sm outline-none focus:border-[#0071e3]"
                >
                  <option value="all">All statuses</option>
                  <option value="open">Open</option>
                  <option value="investigating">Investigating</option>
                  <option value="resolved">Resolved</option>
                  <option value="ignored">Ignored</option>
                </select>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead className="bg-[#fafafa]">
                    <tr className="border-y border-[#f0f0f2] text-[11px] uppercase tracking-wider text-[#a1a1a6]">
                      <th className="px-6 py-3">Incident</th>
                      <th className="px-4 py-3">Count</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-6 py-3">Last seen</th>
                      <th className="px-4 py-3"></th>
                    </tr>
                  </thead>

                  <tbody>
                    {loading ? (
                      <tr>
                        <td colSpan="5" className="px-6 py-12 text-center text-sm text-[#86868b]">
                          Loading incidents...
                        </td>
                      </tr>
                    ) : filteredIncidents.length === 0 ? (
                      <tr>
                        <td colSpan="5" className="px-6 py-12 text-center text-sm text-[#86868b]">
                          No incidents found.
                        </td>
                      </tr>
                    ) : (
                      filteredIncidents.slice(0, 8).map((incident) => (
                        <tr
                          key={incident.id}
                          onClick={() => navigate(`/incidents/${incident.id}`)}
                          className="cursor-pointer border-b border-[#f0f0f2] transition hover:bg-[#f5f8fc]"
                        >
                          <td className="px-6 py-4">
                            <p className="max-w-[260px] truncate text-sm font-medium text-[#1d1d1f]">
                              {incident.title || 'Untitled incident'}
                            </p>
                            <p className="mt-1 text-xs text-[#86868b]">
                              {incident.service_name || 'Unknown service'} · {incident.environment || 'Unknown environment'}
                            </p>
                          </td>

                          <td className="px-4 py-4 text-sm text-[#6e6e73]">
                            {incident.occurrence_count ?? 0}
                          </td>

                          <td className="px-4 py-4">
                            <span className={`text-xs font-medium ${
                              incident.status === 'resolved'
                                ? 'text-green-600'
                                : incident.status === 'investigating'
                                  ? 'text-blue-600'
                                  : 'text-orange-600'
                            }`}>
                              {formatStatus(incident.status)}
                            </span>
                          </td>

                          <td className="whitespace-nowrap px-6 py-4 text-xs text-[#86868b]">
                            <span className="flex items-center gap-1.5">
                              <Clock size={13} />
                              {formatRelativeTime(incident.last_seen)}
                            </span>
                          </td>

                          <td className="px-4 py-4">
                            {incident.status !== 'resolved' && (
                              <button
                                onClick={(event) => {
                                  event.stopPropagation()
                                  handleResolveIncident(incident.id)
                                }}
                                disabled={resolvingId === incident.id}
                                title="Resolve incident"
                                className="rounded-md p-2 text-[#86868b] hover:bg-green-50 hover:text-green-600 disabled:opacity-40"
                              >
                                {resolvingId === incident.id
                                  ? <RefreshCw size={15} className="animate-spin" />
                                  : <CheckCircle size={15} />
                                }
                              </button>
                            )}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              <div className="border-t border-[#f0f0f2] px-6 py-3 text-xs text-[#86868b]">
                Showing {Math.min(filteredIncidents.length, 8)} of {filteredIncidents.length} matching incidents
              </div>
            </div>

            {/* Infrastructure health */}
            <div className="settings-panel min-w-0 overflow-hidden xl:col-span-4">
              <div className="border-b border-[#e5e5ea] px-6 py-5">
                <h2 className="text-base font-semibold text-[#1d1d1f]">
                  Container health
                </h2>
                <p className="mt-1 text-xs text-[#86868b]">
                  Current discovered infrastructure
                </p>
              </div>

              <div className="p-6">
                <div className="mb-5 rounded-xl bg-[#f5f5f7] p-4">
                  <div className="flex items-center gap-2">
                    <span className={`h-2 w-2 rounded-full ${
                      infrastructure.total > 0 && infrastructure.stopped === 0
                        ? 'bg-green-500'
                        : 'bg-orange-500'
                    }`} />
                    <p className="text-sm font-semibold text-[#1d1d1f]">
                      {infrastructure.total === 0
                        ? 'No containers discovered'
                        : infrastructure.stopped === 0
                          ? 'All discovered containers running'
                          : 'Some containers are inactive'}
                    </p>
                  </div>

                  <p className="mt-2 text-xs leading-5 text-[#86868b]">
                    {infrastructure.running} of {infrastructure.total} discovered containers are currently running.
                  </p>
                </div>

                {[
                  {
                    label: 'Running',
                    count: infrastructure.running,
                    color: 'bg-green-500',
                  },
                  {
                    label: 'Stopped / inactive',
                    count: infrastructure.stopped,
                    color: 'bg-orange-500',
                  },
                ].map((item) => {
                  const percentage = infrastructure.total
                    ? (item.count / infrastructure.total) * 100
                    : 0

                  return (
                    <div key={item.label} className="mb-5">
                      <div className="mb-2 flex justify-between text-sm">
                        <span className="text-[#6e6e73]">{item.label}</span>
                        <span className="font-semibold text-[#1d1d1f]">{item.count}</span>
                      </div>
                      <div className="h-1.5 overflow-hidden rounded-full bg-[#f0f0f2]">
                        <div
                          className={`h-full rounded-full ${item.color}`}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  )
                })}

                <button
                  onClick={() => navigate('/containers')}
                  className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg border border-[#e5e5ea] py-2.5 text-sm font-medium text-[#1d1d1f] transition hover:bg-[#f5f5f7]"
                >
                  <Container size={15} />
                  View all containers
                </button>

                <div className="mt-6 border-t border-[#e5e5ea] pt-4">
                  <p className="text-xs text-[#86868b]">Last updated</p>
                  <p className="mt-1 text-sm font-medium text-[#1d1d1f]">
                    {lastUpdated ? lastUpdated.toLocaleTimeString() : '—'}
                  </p>
                  <p className="mt-1 text-xs text-[#a1a1a6]">
                    Automatic refresh every 30 seconds
                  </p>
                </div>
              </div>
            </div>
          </section>

          <footer className="mt-10 flex justify-between border-t border-[#e5e5ea] pt-5 text-xs text-[#a1a1a6]">
            <p>RuntimeRCA © 2026</p>
            <p>Built for reliable applications.</p>
          </footer>
        </div>
      </main>
    </div>
  )
}

export default Dashboard
