import {
  AlertTriangle,
  Activity,
  CheckCircle,
  Bug,
  ArrowUpRight,
  ArrowRight,
  Clock,
  MoreHorizontal,
} from 'lucide-react'

import { useState } from 'react'
import Sidebar from '../components/layout/Sidebar'
import Navbar from '../components/layout/Navbar'
import StatisticsCard from '../components/ui/StatisticsCard'

const initialIncidents = [
  {
    id: 'INC-1042',
    title: 'Database connection timeout',
    service: 'Payment Service',
    environment: 'Production',
    severity: 'Critical',
    status: 'Investigating',
    time: '2 minutes ago',
  },
  {
    id: 'INC-1041',
    title: 'Authentication token expired',
    service: 'Auth Service',
    environment: 'Production',
    severity: 'High',
    status: 'Open',
    time: '18 minutes ago',
  },
  {
    id: 'INC-1040',
    title: 'Redis connection refused',
    service: 'Cache Service',
    environment: 'Production',
    severity: 'Medium',
    status: 'Resolved',
    time: '1 hour ago',
  },
  {
    id: 'INC-1039',
    title: 'Unexpected null reference',
    service: 'User Service',
    environment: 'Development',
    severity: 'Low',
    status: 'Resolved',
    time: '3 hours ago',
  },
]

function Dashboard() {
  const [incidents, setIncidents] = useState(initialIncidents)
  const [filter, setFilter] = useState('All')
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const filteredIncidents =
    filter === 'All'
      ? incidents
      : incidents.filter((incident) => incident.status === filter)

  const resolveIncident = (id) => {
    setIncidents((previous) =>
      previous.map((incident) =>
        incident.id === id
          ? { ...incident, status: 'Resolved' }
          : incident
      )
    )
  }

  const openCount = incidents.filter(
    (incident) => incident.status !== 'Resolved'
  ).length

  const resolvedCount = incidents.filter(
    (incident) => incident.status === 'Resolved'
  ).length

  return (
    <div className="min-h-screen bg-[#f5f5f7]">

      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <main className="min-h-screen">

        <Navbar
          onMenuClick={() => setSidebarOpen(true)}
        />

        <div className="page-container">

          {/* Welcome section */}
          <section className="page-section flex flex-col justify-between gap-6 sm:flex-row sm:items-end">

            <div>
              <p className="mb-2 text-sm font-medium text-[#86868b]">
                Monday, November 24, 2026
              </p>

              <h1 className="text-[32px] font-semibold tracking-[-0.04em] leading-tight text-[#1d1d1f]">
                Overview
              </h1>

              <p className="mt-2 max-w-xl text-[15px] leading-6 text-[#86868b]">
                Monitor your applications, investigate incidents and understand system health.
              </p>
            </div>

            <button className="flex items-center gap-2 rounded-lg bg-[#0071e3] px-4 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-[#0077ed]">
              <Activity size={16} />
              View activity
            </button>

          </section>

          {/* Statistics */}
          <section className="page-section grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">

            <StatisticsCard
              title="Total Incidents"
              value="128"
              icon={Bug}
              color="bg-[#e8f1fc] text-[#0071e3]"
              description="Across all applications"
            />

            <StatisticsCard
              title="Open Incidents"
              value={openCount}
              icon={AlertTriangle}
              color="bg-[#fff0e5] text-[#ff9500]"
              description="Require your attention"
            />

            <StatisticsCard
              title="Resolved Incidents"
              value={resolvedCount}
              icon={CheckCircle}
              color="bg-[#e8f8ed] text-[#34a853]"
              description="Successfully resolved"
            />

            <StatisticsCard
              title="Active Services"
              value="12"
              icon={Activity}
              color="bg-[#f0eafa] text-[#8e5ce6]"
              description="Currently being monitored"
            />

          </section>

          {/* Main content grid */}
          <section className="grid grid-cols-1 items-start gap-6 xl:grid-cols-12">

            {/* Incident table */}
            <div className="overflow-hidden rounded-2xl border border-[#e5e5ea] bg-white xl:col-span-8">

              <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#e5e5ea] px-6 py-5">

                <div>
                  <h2 className="text-base font-semibold text-[#1d1d1f]">
                    Recent incidents
                  </h2>

                  <p className="mt-1 text-xs text-[#86868b]">
                    Monitor and manage your latest errors.
                  </p>
                </div>

                <button className="flex items-center gap-2 text-sm font-medium text-[#0071e3] hover:underline">
                  View all
                  <ArrowRight size={15} />
                </button>

              </div>

              {/* Filters */}
              <div className="flex gap-2 px-6 py-4">

                {['All', 'Open', 'Investigating', 'Resolved'].map((item) => (
                  <button
                    key={item}
                    onClick={() => setFilter(item)}
                    className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                      filter === item
                        ? 'bg-[#1d1d1f] text-white'
                        : 'bg-[#f5f5f7] text-[#6e6e73] hover:bg-[#e5e5ea]'
                    }`}
                  >
                    {item}
                  </button>
                ))}

              </div>

              {/* Table */}
              <div className="overflow-x-auto">

                <table className="w-full text-left">

                  <thead>
                    <tr className="border-y border-[#f0f0f2] bg-[#fafafa] text-[11px] font-medium uppercase tracking-wider text-[#a1a1a6]">
                      <th className="px-6 py-3">Incident</th>
                      <th className="px-4 py-3">Severity</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-6 py-3">Time</th>
                      <th className="px-4 py-3"></th>
                    </tr>
                  </thead>

                  <tbody>
                    {filteredIncidents.map((incident) => (
                      <tr
                        key={incident.id}
                        className="border-b border-[#f0f0f2] transition hover:bg-[#fafafa]"
                      >

                        <td className="px-6 py-4">
                          <p className="max-w-[260px] truncate text-sm font-medium text-[#1d1d1f]">
                            {incident.title}
                          </p>

                          <p className="mt-1 text-xs text-[#86868b]">
                            {incident.id} · {incident.service}
                          </p>
                        </td>

                        <td className="px-4 py-4">
                          <span className={`rounded-md px-2 py-1 text-xs font-medium ${
                            incident.severity === 'Critical'
                              ? 'bg-[#fff0ef] text-[#ff3b30]'
                              : incident.severity === 'High'
                                ? 'bg-[#fff4e5] text-[#e58a00]'
                                : incident.severity === 'Medium'
                                  ? 'bg-[#fff9e6] text-[#b88a00]'
                                  : 'bg-[#f0f0f2] text-[#6e6e73]'
                          }`}>
                            {incident.severity}
                          </span>
                        </td>

                        <td className="px-4 py-4">
                          <span className={`flex w-fit items-center gap-1.5 text-xs font-medium ${
                            incident.status === 'Resolved'
                              ? 'text-[#34a853]'
                              : incident.status === 'Investigating'
                                ? 'text-[#0071e3]'
                                : 'text-[#e58a00]'
                          }`}>
                            <span className="h-1.5 w-1.5 rounded-full bg-current" />
                            {incident.status}
                          </span>
                        </td>

                        <td className="whitespace-nowrap px-6 py-4 text-xs text-[#86868b]">
                          <span className="flex items-center gap-1.5">
                            <Clock size={13} />
                            {incident.time}
                          </span>
                        </td>

                        <td className="px-4 py-4">
                          {incident.status !== 'Resolved' ? (
                            <button
                              onClick={() => resolveIncident(incident.id)}
                              title="Mark as resolved"
                              className="rounded-md p-2 text-[#86868b] transition hover:bg-[#e8f8ed] hover:text-[#34a853]"
                            >
                              <CheckCircle size={16} />
                            </button>
                          ) : (
                            <MoreHorizontal size={17} className="text-[#a1a1a6]" />
                          )}
                        </td>

                      </tr>
                    ))}

                    {filteredIncidents.length === 0 && (
                      <tr>
                        <td colSpan="5" className="px-6 py-12 text-center text-sm text-[#86868b]">
                          No incidents found.
                        </td>
                      </tr>
                    )}

                  </tbody>
                </table>

              </div>
            </div>

            {/* Activity panel */}
            <div className="rounded-2xl border border-[#e5e5ea] bg-white p-6 xl:col-span-4">

              <div className="mb-7 flex items-center justify-between">
                <div>
                  <h2 className="text-base font-semibold text-[#1d1d1f]">
                    System health
                  </h2>

                  <p className="mt-1 text-xs text-[#86868b]">
                    Current platform status
                  </p>
                </div>

                <MoreHorizontal size={19} className="text-[#86868b]" />
              </div>

              <div className="mb-8 rounded-xl bg-[#eaf8ef] p-4">

                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-[#34c759]" />

                  <p className="text-sm font-semibold text-[#248a45]">
                    All systems operational
                  </p>
                </div>

                <p className="mt-2 text-xs leading-5 text-[#578a68]">
                  Your monitored services are running normally.
                </p>

              </div>

              <div className="space-y-6">

                <div>
                  <div className="mb-2 flex justify-between">
                    <span className="text-sm text-[#6e6e73]">
                      API availability
                    </span>

                    <span className="text-sm font-semibold text-[#1d1d1f]">
                      99.98%
                    </span>
                  </div>

                  <div className="h-1.5 overflow-hidden rounded-full bg-[#f0f0f2]">
                    <div className="h-full w-[99.98%] rounded-full bg-[#34c759]" />
                  </div>
                </div>

                <div>
                  <div className="mb-2 flex justify-between">
                    <span className="text-sm text-[#6e6e73]">
                      Error rate
                    </span>

                    <span className="text-sm font-semibold text-[#1d1d1f]">
                      0.02%
                    </span>
                  </div>

                  <div className="h-1.5 overflow-hidden rounded-full bg-[#f0f0f2]">
                    <div className="h-full w-[2%] rounded-full bg-[#0071e3]" />
                  </div>
                </div>

                <div>
                  <div className="mb-2 flex justify-between">
                    <span className="text-sm text-[#6e6e73]">
                      Service uptime
                    </span>

                    <span className="text-sm font-semibold text-[#1d1d1f]">
                      99.9%
                    </span>
                  </div>

                  <div className="h-1.5 overflow-hidden rounded-full bg-[#f0f0f2]">
                    <div className="h-full w-[99.9%] rounded-full bg-[#34c759]" />
                  </div>
                </div>

              </div>

              <div className="mt-8 border-t border-[#e5e5ea] pt-5">

                <div className="flex items-center justify-between">
                  <p className="text-xs text-[#86868b]">
                    Last updated
                  </p>

                  <p className="text-xs font-medium text-[#1d1d1f]">
                    Just now
                  </p>
                </div>

                <button className="mt-5 flex w-full items-center justify-center gap-2 rounded-lg border border-[#e5e5ea] py-2.5 text-sm font-medium text-[#1d1d1f] transition hover:bg-[#f5f5f7]">
                  View system details
                  <ArrowUpRight size={15} />
                </button>

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