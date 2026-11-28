import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AlertTriangle,
  Clock,
  Search,
  RefreshCw,
  Bug,
  CheckCircle,
} from 'lucide-react'

import Sidebar from '../components/layout/Sidebar'
import Navbar from '../components/layout/Navbar'
import { getIncidents } from '../services/incidentService'

function formatTime(value) {
  if (!value) return 'Unknown'

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Unknown'

  return date.toLocaleString()
}

function statusStyle(status) {
  const styles = {
    open: 'bg-orange-50 text-orange-600',
    investigating: 'bg-blue-50 text-blue-600',
    resolved: 'bg-green-50 text-green-600',
    ignored: 'bg-gray-100 text-gray-600',
  }

  return styles[status] || 'bg-gray-100 text-gray-600'
}

function Incidents() {
  const navigate = useNavigate()

  const [incidents, setIncidents] = useState([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const fetchIncidents = useCallback(async (manual = false) => {
    if (manual) setRefreshing(true)

    try {
      setError('')
      const data = await getIncidents()
      setIncidents(data.results || [])
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Unable to load incidents.'
      )
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [])

  useEffect(() => {
    fetchIncidents()

    const interval = setInterval(() => fetchIncidents(), 30000)
    return () => clearInterval(interval)
  }, [fetchIncidents])

  const filteredIncidents = useMemo(() => {
    return incidents.filter((incident) => {
      const query = search.toLowerCase()

      const matchesSearch =
        incident.title?.toLowerCase().includes(query) ||
        incident.service_name?.toLowerCase().includes(query) ||
        incident.environment?.toLowerCase().includes(query) ||
        incident.exception_type?.toLowerCase().includes(query)

      const matchesStatus =
        statusFilter === 'all' || incident.status === statusFilter

      return matchesSearch && matchesStatus
    })
  }, [incidents, search, statusFilter])

  const counts = useMemo(() => ({
    total: incidents.length,
    open: incidents.filter((i) => i.status === 'open').length,
    investigating: incidents.filter((i) => i.status === 'investigating').length,
    resolved: incidents.filter((i) => i.status === 'resolved').length,
  }), [incidents])

  return (
    <div className="min-h-screen bg-[#f5f5f7]">
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <main className="min-h-screen">
        <Navbar onMenuClick={() => setSidebarOpen(true)} />

        <div className="page-container">
          <section className="mb-8 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
            <div>
              <p className="mb-2 text-sm text-[#86868b]">
                Application monitoring
              </p>

              <h1 className="text-[32px] font-semibold tracking-[-0.04em] text-[#1d1d1f]">
                Incidents
              </h1>

              <p className="mt-2 text-sm text-[#86868b]">
                Investigate errors and monitor application reliability.
              </p>
            </div>

            <button
              onClick={() => fetchIncidents(true)}
              disabled={refreshing}
              className="flex items-center gap-2 rounded-lg bg-[#0071e3] px-4 py-2.5 text-sm font-medium text-white hover:bg-[#0077ed] disabled:opacity-50"
            >
              <RefreshCw
                size={16}
                className={refreshing ? 'animate-spin' : ''}
              />
              Refresh
            </button>
          </section>

          {error && (
            <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
              {error}
            </div>
          )}

          <section className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {[
              { label: 'Total incidents', value: counts.total, icon: Bug },
              { label: 'Open', value: counts.open, icon: AlertTriangle },
              { label: 'Investigating', value: counts.investigating, icon: RefreshCw },
              { label: 'Resolved', value: counts.resolved, icon: CheckCircle },
            ].map((item) => {
              const Icon = item.icon

              return (
                <div key={item.label} className="settings-panel p-5">
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-[#86868b]">{item.label}</p>
                    <Icon size={18} className="text-[#0071e3]" />
                  </div>

                  <p className="mt-3 text-3xl font-semibold text-[#1d1d1f]">
                    {loading ? '—' : item.value}
                  </p>
                </div>
              )
            })}
          </section>

          <section className="settings-panel overflow-hidden">
            <div className="flex flex-col gap-3 border-b border-[#e5e5ea] p-5 sm:flex-row">
              <div className="relative flex-1">
                <Search
                  size={17}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-[#a1a1a6]"
                />

                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search incidents, services..."
                  className="w-full rounded-lg border border-[#e5e5ea] bg-white py-2.5 pl-10 pr-4 text-sm outline-none focus:border-[#0071e3]"
                />
              </div>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="rounded-lg border border-[#e5e5ea] bg-white px-4 py-2.5 text-sm outline-none focus:border-[#0071e3]"
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
                  <tr className="border-b border-[#f0f0f2] text-[11px] uppercase tracking-wider text-[#a1a1a6]">
                    <th className="px-6 py-4">Incident</th>
                    <th className="px-4 py-4">Occurrences</th>
                    <th className="px-4 py-4">Status</th>
                    <th className="px-6 py-4">Last seen</th>
                  </tr>
                </thead>

                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan="4" className="px-6 py-14 text-center text-sm text-[#86868b]">
                        Loading incidents...
                      </td>
                    </tr>
                  ) : filteredIncidents.length === 0 ? (
                    <tr>
                      <td colSpan="4" className="px-6 py-14 text-center text-sm text-[#86868b]">
                        No incidents found.
                      </td>
                    </tr>
                  ) : (
                    filteredIncidents.map((incident) => (
                      <tr
                        key={incident.id}
                        onClick={() => navigate(`/incidents/${incident.id}`)}
                        className="cursor-pointer border-b border-[#f0f0f2] transition hover:bg-[#f5f8fc]"
                      >
                        <td className="px-6 py-4">
                          <p className="max-w-md truncate text-sm font-medium text-[#1d1d1f]">
                            {incident.title || incident.exception_type || 'Untitled incident'}
                          </p>

                          <p className="mt-1 text-xs text-[#86868b]">
                            {incident.service_name || 'Unknown service'}
                            {' · '}
                            {incident.environment || 'Unknown environment'}
                          </p>
                        </td>

                        <td className="px-4 py-4 text-sm text-[#6e6e73]">
                          {incident.occurrence_count ?? 0}
                        </td>

                        <td className="px-4 py-4">
                          <span className={`rounded-full px-2.5 py-1 text-xs font-medium capitalize ${statusStyle(incident.status)}`}>
                            {incident.status || 'unknown'}
                          </span>
                        </td>

                        <td className="whitespace-nowrap px-6 py-4 text-xs text-[#86868b]">
                          <span className="flex items-center gap-2">
                            <Clock size={13} />
                            {formatTime(incident.last_seen)}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            <div className="border-t border-[#f0f0f2] px-6 py-4 text-xs text-[#86868b]">
              Showing {filteredIncidents.length} of {incidents.length} incidents
              <span className="float-right">Auto-refresh: 30 seconds</span>
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}

export default Incidents