import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import {
  ArrowLeft,
  AlertCircle,
  CheckCircle,
  Clock,
  Server,
  Activity,
  RefreshCw,
  Terminal,
  ShieldCheck,
  Lightbulb,
  FileText,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'

import Sidebar from '../components/layout/Sidebar'
import Navbar from '../components/layout/Navbar'

import {
  getIncidentDetails,
  getInvestigation,
  resolveIncident,
  reopenIncident,
} from '../services/incidentService'


function formatDate(dateString) {
  if (!dateString) return 'Unavailable'

  return new Date(dateString).toLocaleString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}


function formatStatus(status) {
  if (!status) return 'Unknown'

  return status.charAt(0).toUpperCase() + status.slice(1).toLowerCase()
}


function StatusBadge({ status }) {
  const styles = {
    open: 'bg-[#fff4e5] text-[#b76e00]',
    investigating: 'bg-[#e8f1fc] text-[#0071e3]',
    resolved: 'bg-[#e8f8ed] text-[#248a3d]',
    ignored: 'bg-[#f0f0f2] text-[#6e6e73]',
    completed: 'bg-[#e8f8ed] text-[#248a3d]',
    pending: 'bg-[#fff4e5] text-[#b76e00]',
    running: 'bg-[#e8f1fc] text-[#0071e3]',
    failed: 'bg-[#fff0ef] text-[#d92d20]',
  }

  return (
    <span
      className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium ${
        styles[status?.toLowerCase()] || 'bg-[#f5f5f7] text-[#6e6e73]'
      }`}
    >
      {formatStatus(status)}
    </span>
  )
}


function MetricCard({ label, value, icon: Icon, description }) {
  return (
    <div className="rounded-2xl border border-[#e5e5ea] bg-white p-5">
      <div className="flex items-center justify-between">
        <p className="text-sm text-[#86868b]">{label}</p>
        <Icon size={18} className="text-[#86868b]" />
      </div>

      <p className="mt-4 text-2xl font-semibold tracking-tight text-[#1d1d1f]">
        {value}
      </p>

      <p className="mt-1 text-xs text-[#86868b]">{description}</p>
    </div>
  )
}


function IncidentDetail() {
  const { incidentId } = useParams()
  const navigate = useNavigate()

  const [sidebarOpen, setSidebarOpen] = useState(false)

  const [incident, setIncident] = useState(null)
  const [investigation, setInvestigation] = useState(null)

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)

  const [expandedEvents, setExpandedEvents] = useState({})

  const fetchDetails = async () => {
    try {
      setLoading(true)
      setError(null)

      const [incidentData, investigationData] = await Promise.all([
        getIncidentDetails(incidentId),
        getInvestigation(incidentId),
      ])

      setIncident(incidentData)
      setInvestigation(investigationData)

    } catch (err) {
      console.error('Failed to load incident:', err)

      setError(
        err.response?.data?.detail ||
        'Unable to load incident details.'
      )

    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDetails()
  }, [incidentId])

  const handleStatusChange = async () => {
    try {
      setActionLoading(true)

      if (incident.status === 'resolved') {
        await reopenIncident(incidentId)
      } else {
        await resolveIncident(incidentId)
      }

      await fetchDetails()

    } catch (err) {
      console.error('Failed to update incident:', err)

      setError(
        err.response?.data?.detail ||
        'Unable to update incident status.'
      )

    } finally {
      setActionLoading(false)
    }
  }

  const toggleEvent = (eventId) => {
    setExpandedEvents((previous) => ({
      ...previous,
      [eventId]: !previous[eventId],
    }))
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#f5f5f7]">
        <div className="flex items-center gap-3 text-sm text-[#86868b]">
          <RefreshCw size={18} className="animate-spin" />
          Loading incident details...
        </div>
      </div>
    )
  }

  if (error || !incident) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#f5f5f7] p-6">
        <div className="max-w-md rounded-2xl border border-[#e5e5ea] bg-white p-8 text-center">
          <AlertCircle size={32} className="mx-auto text-[#ff3b30]" />

          <h2 className="mt-4 text-lg font-semibold text-[#1d1d1f]">
            Unable to load incident
          </h2>

          <p className="mt-2 text-sm text-[#86868b]">
            {error || 'Incident not found.'}
          </p>

          <button
            onClick={() => navigate('/')}
            className="mt-6 rounded-lg bg-[#0071e3] px-4 py-2 text-sm font-medium text-white"
          >
            Back to dashboard
          </button>
        </div>
      </div>
    )
  }

  const events = incident.recent_events || []

  return (
    <div className="min-h-screen bg-[#f5f5f7]">

      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <main className="min-h-screen">

        <Navbar onMenuClick={() => setSidebarOpen(true)} />

        <div className="page-container">

          {/* Back navigation */}
          <button
            onClick={() => navigate('/')}
            className="mb-7 flex items-center gap-2 text-sm font-medium text-[#86868b] transition hover:text-[#0071e3]"
          >
            <ArrowLeft size={16} />
            Back to incidents
          </button>

          {/* Incident heading */}
          <section className="page-section">

            <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-start">

              <div className="min-w-0">

                <div className="mb-3 flex flex-wrap items-center gap-3">
                  <StatusBadge status={incident.status} />

                  <span className="text-xs text-[#86868b]">
                    {incident.environment}
                  </span>

                  <span className="text-xs text-[#86868b]">
                    ID: {incident.id.slice(0, 8)}
                  </span>
                </div>

                <h1 className="max-w-4xl break-words text-2xl font-semibold tracking-tight text-[#1d1d1f] sm:text-3xl">
                  {incident.title}
                </h1>

                <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-[#86868b]">

                  <span className="flex items-center gap-2">
                    <Server size={15} />
                    {incident.service_name}
                  </span>

                  <span className="flex items-center gap-2">
                    <Activity size={15} />
                    {incident.environment}
                  </span>

                </div>

              </div>

              <div className="flex shrink-0 gap-2">

                <button
                  onClick={fetchDetails}
                  className="flex items-center gap-2 rounded-lg border border-[#e5e5ea] bg-white px-4 py-2.5 text-sm font-medium text-[#1d1d1f] hover:bg-[#fafafa]"
                >
                  <RefreshCw size={15} />
                  Refresh
                </button>

                <button
                  onClick={handleStatusChange}
                  disabled={actionLoading}
                  className={`flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium text-white disabled:opacity-50 ${
                    incident.status === 'resolved'
                      ? 'bg-[#0071e3] hover:bg-[#0077ed]'
                      : 'bg-[#34a853] hover:bg-[#248a3d]'
                  }`}
                >
                  {actionLoading ? (
                    <RefreshCw size={15} className="animate-spin" />
                  ) : (
                    <CheckCircle size={15} />
                  )}

                  {incident.status === 'resolved'
                    ? 'Reopen incident'
                    : 'Resolve incident'}
                </button>

              </div>

            </div>

          </section>

          {/* Incident metrics */}
          <section className="page-section grid grid-cols-1 gap-4 sm:grid-cols-3">

            <MetricCard
              label="Occurrences"
              value={incident.occurrence_count}
              icon={Activity}
              description="Total recorded occurrences"
            />

            <MetricCard
              label="First seen"
              value={formatDate(incident.first_seen)}
              icon={Clock}
              description="Initial occurrence"
            />

            <MetricCard
              label="Last seen"
              value={formatDate(incident.last_seen)}
              icon={Clock}
              description="Most recent occurrence"
            />

          </section>

          {/* Investigation */}
          <section className="page-section">

            <div className="mb-5 flex flex-wrap items-center justify-between gap-3">

              <div>
                <h2 className="text-xl font-semibold tracking-tight text-[#1d1d1f]">
                  Root cause investigation
                </h2>

                <p className="mt-1 text-sm text-[#86868b]">
                  Automated analysis of the incident and its evidence.
                </p>
              </div>

              {investigation && (
                <StatusBadge status={investigation.status} />
              )}

            </div>

            {!investigation ? (

              <div className="rounded-2xl border border-[#e5e5ea] bg-white p-8 text-center">

                <Lightbulb size={28} className="mx-auto text-[#86868b]" />

                <h3 className="mt-3 font-semibold text-[#1d1d1f]">
                  No investigation available
                </h3>

                <p className="mt-2 text-sm text-[#86868b]">
                  An investigation report has not been generated for this incident.
                </p>

              </div>

            ) : (

              <div className="space-y-5">

                {/* Summary */}
                <div className="rounded-2xl border border-[#e5e5ea] bg-white p-6">

                  <div className="mb-4 flex items-center gap-2">
                    <FileText size={18} className="text-[#0071e3]" />

                    <h3 className="font-semibold text-[#1d1d1f]">
                      Investigation summary
                    </h3>
                  </div>

                  <p className="text-sm leading-7 text-[#515154]">
                    {investigation.summary || 'No summary available.'}
                  </p>

                  <div className="mt-5 flex flex-wrap gap-5 border-t border-[#f0f0f2] pt-4 text-xs text-[#86868b]">

                    <span>
                      Started: {formatDate(investigation.created_at)}
                    </span>

                    <span>
                      Completed: {formatDate(investigation.completed_at)}
                    </span>

                  </div>

                </div>

                {/* Hypotheses */}
                <div className="rounded-2xl border border-[#e5e5ea] bg-white p-6">

                  <div className="mb-5 flex items-center gap-2">
                    <Lightbulb size={18} className="text-[#ff9f0a]" />

                    <h3 className="font-semibold text-[#1d1d1f]">
                      Root cause hypotheses
                    </h3>
                  </div>

                  {investigation.hypotheses?.length ? (

                    <div className="space-y-5">

                      {investigation.hypotheses.map((hypothesis, index) => {

                        const confidence = Math.round(
                          (hypothesis.confidence || 0) * 100
                        )

                        return (

                          <div key={index}>

                            <div className="mb-2 flex flex-wrap items-center justify-between gap-2">

                              <p className="text-sm font-medium text-[#1d1d1f]">
                                {hypothesis.cause}
                              </p>

                              <span className="text-sm font-semibold text-[#6e6e73]">
                                {confidence}% confidence
                              </span>

                            </div>

                            <div className="h-2 overflow-hidden rounded-full bg-[#f0f0f2]">

                              <div
                                className="h-full rounded-full bg-[#0071e3] transition-all"
                                style={{
                                  width: `${Math.min(100, confidence)}%`,
                                }}
                              />

                            </div>

                          </div>

                        )
                      })}

                    </div>

                  ) : (

                    <p className="text-sm text-[#86868b]">
                      No hypotheses were generated.
                    </p>

                  )}

                  <p className="mt-5 text-xs leading-5 text-[#86868b]">
                    Confidence scores are heuristic estimates produced by the current rule-based RCA engine. They are not statistically calibrated probabilities.
                  </p>

                </div>

                {/* Evidence */}
                <div className="rounded-2xl border border-[#e5e5ea] bg-white p-6">

                  <div className="mb-5 flex items-center gap-2">
                    <ShieldCheck size={18} className="text-[#34a853]" />

                    <h3 className="font-semibold text-[#1d1d1f]">
                      Investigation evidence
                    </h3>
                  </div>

                  {investigation.evidence?.length ? (

                    <ul className="space-y-3">

                      {investigation.evidence.map((item, index) => (

                        <li
                          key={index}
                          className="flex gap-3 text-sm leading-6 text-[#515154]"
                        >
                          <CheckCircle
                            size={16}
                            className="mt-1 shrink-0 text-[#34a853]"
                          />

                          {item}
                        </li>

                      ))}

                    </ul>

                  ) : (

                    <p className="text-sm text-[#86868b]">
                      No evidence recorded.
                    </p>

                  )}

                </div>

                {/* Recommended actions */}
                <div className="rounded-2xl border border-[#e5e5ea] bg-white p-6">

                  <div className="mb-5 flex items-center gap-2">
                    <CheckCircle size={18} className="text-[#0071e3]" />

                    <h3 className="font-semibold text-[#1d1d1f]">
                      Recommended actions
                    </h3>
                  </div>

                  {investigation.recommended_actions?.length ? (

                    <div className="space-y-3">

                      {investigation.recommended_actions.map((action, index) => (

                        <div
                          key={index}
                          className="flex items-start gap-3 rounded-xl bg-[#f5f5f7] p-4"
                        >

                          <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-white text-xs font-semibold text-[#0071e3]">
                            {index + 1}
                          </span>

                          <p className="text-sm leading-6 text-[#515154]">
                            {action}
                          </p>

                        </div>

                      ))}

                    </div>

                  ) : (

                    <p className="text-sm text-[#86868b]">
                      No recommended actions available.
                    </p>

                  )}

                </div>

              </div>

            )}

          </section>

          {/* Event timeline */}
          <section className="page-section">

            <div className="mb-5">

              <h2 className="text-xl font-semibold tracking-tight text-[#1d1d1f]">
                Event timeline
              </h2>

              <p className="mt-1 text-sm text-[#86868b]">
                Individual error events associated with this incident.
              </p>

            </div>

            <div className="rounded-2xl border border-[#e5e5ea] bg-white p-6">

              {events.length ? (

                <div className="space-y-5">

                  {events.map((event) => (

                    <div
                      key={event.id}
                      className="border-b border-[#f0f0f2] pb-5 last:border-0 last:pb-0"
                    >

                      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">

                        <div className="flex gap-3">

                          <div className="mt-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[#fff0ef]">
                            <AlertCircle size={17} className="text-[#ff3b30]" />
                          </div>

                          <div className="min-w-0">

                            <p className="text-sm font-medium text-[#1d1d1f]">
                              {event.exception_type || 'Runtime error'}
                            </p>

                            <p className="mt-1 break-words text-sm text-[#6e6e73]">
                              {event.message}
                            </p>

                            <p className="mt-2 text-xs text-[#a1a1a6]">
                              {formatDate(event.occurred_at)}
                            </p>

                          </div>

                        </div>

                        {event.stack_trace && (

                          <button
                            onClick={() => toggleEvent(event.id)}
                            className="flex shrink-0 items-center gap-2 text-xs font-medium text-[#0071e3] hover:underline"
                          >
                            <Terminal size={14} />
                            {expandedEvents[event.id]
                              ? 'Hide stack trace'
                              : 'View stack trace'}

                            {expandedEvents[event.id]
                              ? <ChevronUp size={14} />
                              : <ChevronDown size={14} />}
                          </button>

                        )}

                      </div>

                      {expandedEvents[event.id] && (

                        <pre className="mt-4 overflow-x-auto rounded-xl bg-[#1d1d1f] p-4 text-xs leading-6 text-[#e5e5ea]">
                          {event.stack_trace}
                        </pre>

                      )}

                    </div>

                  ))}

                </div>

              ) : (

                <p className="py-6 text-center text-sm text-[#86868b]">
                  No individual events available.
                </p>

              )}

            </div>

          </section>

          <footer className="mt-10 border-t border-[#e5e5ea] pt-5 text-xs text-[#a1a1a6]">
            Runtime RCA © 2026
          </footer>

        </div>

      </main>

    </div>
  )
}

export default IncidentDetail