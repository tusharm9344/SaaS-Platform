import {
  AlertTriangle,
  Activity,
  CheckCircle,
  Bug,
  ArrowUpRight,
  ArrowRight,
  Clock,
  MoreHorizontal,
  RefreshCw,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'

import Sidebar from '../components/layout/Sidebar'
import Navbar from '../components/layout/Navbar'
import StatisticsCard from '../components/ui/StatisticsCard'

import {
  getIncidents,
  resolveIncident as resolveIncidentAPI,
} from '../services/incidentService'


function formatRelativeTime(dateString) {
  if (!dateString) return 'Unknown'

  const date = new Date(dateString)

  if (Number.isNaN(date.getTime())) return 'Unknown'

  const seconds = Math.floor((Date.now() - date.getTime()) / 1000)

  if (seconds < 60) return 'Just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`
  if (seconds < 604800) return `${Math.floor(seconds / 86400)} days ago`

  return date.toLocaleDateString()
}


function formatStatus(status) {
  if (!status) return 'Unknown'

  return status.charAt(0).toUpperCase() + status.slice(1).toLowerCase()
}


function Dashboard() {
  const navigate = useNavigate()
  const [incidents, setIncidents] = useState([])
  const [totalCount, setTotalCount] = useState(0)

  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [resolvingId, setResolvingId] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)

  const statistics = useMemo(() => {
    return {
      total: incidents.length,
      open: incidents.filter(
        (incident) => incident.status === 'open'
      ).length,
      resolved: incidents.filter(
        (incident) => incident.status === 'resolved'
      ).length,
      ignored: incidents.filter(
        (incident) => incident.status === 'ignored'
      ).length,
    }
  }, [incidents])

  // Fetch real incidents from Django
  const fetchIncidents = async () => {
    try {
      setError(null)

      const data = await getIncidents()

      setIncidents(data.results || [])
      setTotalCount(data.count ?? data.results?.length ?? 0)
      setLastUpdated(new Date())

    } catch (err) {
      console.error('Failed to fetch incidents:', err)

      setError(
        err.response?.data?.detail ||
        'Unable to load incidents. Please check your connection.'
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchIncidents()
  }, [])

  // Statistics
  const investigatingCount = incidents.filter(
    (incident) => incident.status === 'investigating'
  ).length

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

  // Resolve incident through Django API
  const handleResolveIncident = async (incidentId) => {
    try {
      setResolvingId(incidentId)

      await resolveIncidentAPI(incidentId)

      setIncidents((previous) =>
        previous.map((incident) =>
          incident.id === incidentId
            ? { ...incident, status: 'resolved' }
            : incident
        )
      )

      setLastUpdated(new Date())

    } catch (err) {
      console.error('Failed to resolve incident:', err)

      setError(
        err.response?.data?.detail ||
        'Unable to resolve incident. Please try again.'
      )

    } finally {
      setResolvingId(null)
    }
  }

  const today = new Date().toLocaleDateString('en-US', {
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

      <main className="min-h-screen bg-[#f5f5f7]">

        <Navbar
          onMenuClick={() => setSidebarOpen(true)}
        />

        <div className="page-container">

          {/* Welcome section */}
          <section className="page-section flex flex-col justify-between gap-6 sm:flex-row sm:items-end">

            <div>
              <p className="mb-2 text-sm font-medium text-[#86868b]">
                {today}
              </p>

              <h1 className="text-[32px] font-semibold tracking-[-0.04em] leading-tight text-[#1d1d1f]">
                Overview
              </h1>

              <p className="mt-2 max-w-xl text-[15px] leading-6 text-[#86868b]">
                Monitor your applications, investigate incidents and understand system health.
              </p>
            </div>

            <button
              onClick={fetchIncidents}
              disabled={loading}
              className="flex items-center gap-2 rounded-lg bg-[#0071e3] px-4 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-[#0077ed] disabled:opacity-50"
            >
              <RefreshCw
                size={16}
                className={loading ? 'animate-spin' : ''}
              />
              Refresh activity
            </button>

          </section>

          {/* Error message */}
          {error && (
            <div className="mb-6 rounded-xl border border-[#ff3b30]/20 bg-[#fff0ef] px-4 py-3 text-sm text-[#d92d20]">
              {error}
            </div>
          )}

          {/* Statistics */}
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-4">

            <StatisticsCard
              title="Total Incidents"
              value={loading ? '—' : statistics.total}
              icon={Bug}
              color="bg-[#e8f1fc] text-[#0071e3]"
              description="Across all applications"
            />

            <StatisticsCard
              title="Open Incidents"
              value={loading ? '—' : statistics.open}
              icon={AlertTriangle}
              color="bg-[#fff0e5] text-[#ff9500]"
              description="Require your attention"
            />

            <StatisticsCard
              title="Resolved Incidents"
              value={loading ? '—' : statistics.resolved}
              icon={CheckCircle}
              color="bg-[#e8f8ed] text-[#34a853]"
              description="Successfully resolved"
            />

            <StatisticsCard
              title="Ignored Incidents"
              value={loading ? '—' : statistics.ignored}
              icon={Activity}
              color="bg-[#f0eafa] text-[#8e5ce6]"
              description="Incidents marked ignored"
            />

          </div>

          {/* Main content grid */}
          <section className="grid grid-cols-1 items-start gap-6 xl:grid-cols-12">

            {/* Incident table */}
            <div className="settings-panel min-w-0 overflow-hidden xl:col-span-8">

              <div className="flex items-center justify-between gap-4 border-b border-[#e5e5ea] px-7 py-5">

                <div>
                  <h2 className="text-base font-semibold text-[#1d1d1f]">
                    Recent incidents
                  </h2>

                  <p className="mt-1 text-xs text-[#86868b]">
                    Monitor and manage your latest errors.
                  </p>
                </div>

                <button
                  onClick={fetchIncidents}
                  className="flex items-center gap-2 text-sm font-medium text-[#0071e3] hover:underline"
                >
                  Refresh
                  <ArrowRight size={15} />
                </button>

              </div>

              {/* Search and status filters */}
              <div className="mb-5 flex flex-col gap-3 px-6 pt-4 sm:flex-row sm:items-center sm:justify-between">
                <input
                  type="text"
                  placeholder="Search incidents, services..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="min-h-11 w-full rounded-lg border border-[#e5e5ea] bg-white px-4 text-sm outline-none transition focus:border-[#0071e3]"
                />

                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="min-h-11 rounded-lg border border-[#e5e5ea] bg-white px-4 text-sm outline-none focus:border-[#0071e3]"
                >
                  <option value="all">All statuses</option>
                  <option value="open">Open</option>
                  <option value="investigating">Investigating</option>
                  <option value="resolved">Resolved</option>
                  <option value="ignored">Ignored</option>
                </select>
              </div>

              {/* Table */}
              <div className="overflow-x-auto">

                <table className="data-table">

                  <thead>
                    <tr className="border-y border-[#f0f0f2] bg-[#fafafa] text-[11px] font-medium uppercase tracking-wider text-[#a1a1a6]">

                      <th className="px-6 py-3">Incident</th>
                      <th className="px-4 py-3">Occurrences</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-6 py-3">Last seen</th>
                      <th className="px-4 py-3"></th>

                    </tr>
                  </thead>

                  <tbody>

                    {loading ? (

                      <tr>
                        <td
                          colSpan="5"
                          className="px-6 py-12 text-center text-sm text-[#86868b]"
                        >
                          Loading incidents...
                        </td>
                      </tr>

                    ) : filteredIncidents.map((incident) => (

                      <tr
                        key={incident.id}
                        onClick={() => navigate(`/incidents/${incident.id}`)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            navigate(`/incidents/${incident.id}`)
                          }
                        }}
                        role="link"
                        tabIndex={0}
                        className="cursor-pointer border-b border-[#f0f0f2] transition hover:bg-[#f5f8fc] focus:outline-none focus:ring-2 focus:ring-inset focus:ring-[#0071e3]"
                      >

                        <td className="px-6 py-4">

                          <p className="max-w-[280px] truncate text-sm font-medium text-[#1d1d1f]">
                            {incident.title}
                          </p>

                          <p className="mt-1 text-xs text-[#86868b]">
                            {incident.service_name} · {incident.environment}
                          </p>

                        </td>

                        <td className="px-4 py-4">

                          <span className="rounded-md bg-[#f5f5f7] px-2 py-1 text-xs font-medium text-[#6e6e73]">
                            {incident.occurrence_count}
                          </span>

                        </td>

                        <td className="px-4 py-4">

                          <span
                            className={`flex w-fit items-center gap-1.5 text-xs font-medium ${
                              incident.status === 'resolved'
                                ? 'text-[#34a853]'
                                : incident.status === 'investigating'
                                  ? 'text-[#0071e3]'
                                  : 'text-[#e58a00]'
                            }`}
                          >
                            <span className="h-1.5 w-1.5 rounded-full bg-current" />
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

                          {incident.status !== 'resolved' ? (

                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                handleResolveIncident(incident.id)
                              }}
                              onKeyDown={(event) => event.stopPropagation()}
                              disabled={resolvingId === incident.id}
                              title="Mark as resolved"
                              className="rounded-md p-2 text-[#86868b] transition hover:bg-[#e8f8ed] hover:text-[#34a853] disabled:opacity-40"
                            >
                              {resolvingId === incident.id ? (
                                <RefreshCw size={16} className="animate-spin" />
                              ) : (
                                <CheckCircle size={16} />
                              )}
                            </button>

                          ) : (

                            <MoreHorizontal
                              size={17}
                              className="text-[#a1a1a6]"
                            />

                          )}

                        </td>

                      </tr>

                    ))}

                    {!loading && filteredIncidents.length === 0 && (

                      <tr>
                        <td
                          colSpan="5"
                          className="px-6 py-12 text-center text-sm text-[#86868b]"
                        >
                          No incidents found.
                        </td>
                      </tr>

                    )}

                  </tbody>

                </table>

              </div>

              <div className="border-t border-[#f0f0f2] px-6 py-3 text-xs text-[#86868b]">
                Showing {filteredIncidents.length} of {totalCount} incidents
              </div>

            </div>

            {/* Activity panel */}
            <div className="settings-panel min-w-0 overflow-hidden xl:col-span-4">

              <div className="border-b border-[#e5e5ea] px-7 py-5">

                <div className="flex items-center justify-between gap-4">

                  <div>
                    <h2 className="text-base font-semibold text-[#1d1d1f]">
                      Incident overview
                    </h2>

                    <p className="mt-1 text-xs text-[#86868b]">
                      Current incident distribution
                    </p>
                  </div>

                  <MoreHorizontal size={19} className="text-[#86868b]" />

                </div>

              </div>

              <div className="space-y-0 px-7">

                {/* Incident status summary */}
                <div className="mt-5 mb-8 rounded-xl bg-[#f5f5f7] p-4">

                  <div className="flex items-center gap-2">

                    <div className="h-2 w-2 rounded-full bg-[#0071e3]" />

                    <p className="text-sm font-semibold text-[#1d1d1f]">
                      Incident monitoring active
                    </p>

                  </div>

                  <p className="mt-2 text-xs leading-5 text-[#86868b]">
                    Your platform has recorded {totalCount} incidents across its monitored services.
                  </p>

                </div>

                <div className="space-y-0">

                  {[
                    {
                      label: 'Open',
                      count: statistics.open,
                      color: 'bg-[#ff9f0a]',
                    },
                    {
                      label: 'Investigating',
                      count: investigatingCount,
                      color: 'bg-[#0071e3]',
                    },
                    {
                      label: 'Resolved',
                      count: statistics.resolved,
                      color: 'bg-[#34c759]',
                    },
                  ].map((item) => {

                    const percentage = incidents.length
                      ? (item.count / incidents.length) * 100
                      : 0

                    return (

                      <div
                        key={item.label}
                        className="flex min-w-0 items-start gap-3 border-b border-[#f0f0f2] py-5 last:border-b-0"
                      >

                        <div className="min-w-0 flex-1">

                          <div className="mb-2 flex justify-between">

                            <span className="text-sm text-[#6e6e73]">
                              {item.label}
                            </span>

                            <span className="text-sm font-semibold text-[#1d1d1f]">
                              {item.count}
                            </span>

                          </div>

                          <div className="h-1.5 overflow-hidden rounded-full bg-[#f0f0f2]">

                            <div
                              className={`h-full rounded-full ${item.color}`}
                              style={{ width: `${percentage}%` }}
                            />

                          </div>

                        </div>

                      </div>

                    )
                  })}

                </div>

                <div className="mt-8 border-t border-[#e5e5ea] pt-5">

                  <div className="flex items-center justify-between">

                    <p className="text-xs text-[#86868b]">
                      Last updated
                    </p>

                    <p className="text-xs font-medium text-[#1d1d1f]">
                      {lastUpdated
                        ? lastUpdated.toLocaleTimeString()
                        : '—'}
                    </p>

                  </div>

                  <button
                    onClick={fetchIncidents}
                    className="mt-5 flex w-full items-center justify-center gap-2 rounded-lg border border-[#e5e5ea] py-2.5 text-sm font-medium text-[#1d1d1f] transition hover:bg-[#f5f5f7]"
                  >
                    Refresh dashboard
                    <ArrowUpRight size={15} />
                  </button>

                </div>

              </div>

            </div>

          </section>

          {/* Footer */}
          <footer className="mt-10 flex justify-between border-t border-[#e5e5ea] pt-5 text-xs text-[#a1a1a6]">
            <p>Runtime RCA © 2026</p>
            <p>Built for reliable applications.</p>
          </footer>

        </div>

      </main>

    </div>
  )
}

export default Dashboard