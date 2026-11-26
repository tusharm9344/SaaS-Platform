import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Search,
  Bell,
  ChevronDown,
  Menu,
  X,
  Command,
  AlertCircle,
  LoaderCircle,
} from 'lucide-react'

import { getIncidents } from '../../services/incidentService'

function Navbar({ onMenuClick }) {
  const navigate = useNavigate()

  const [searchOpen, setSearchOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [incidents, setIncidents] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const inputRef = useRef(null)

  // Open search with Cmd + K or Ctrl + K
  useEffect(() => {
    const handleKeyDown = (event) => {
      const isShortcut =
        (event.metaKey || event.ctrlKey) &&
        event.key.toLowerCase() === 'k'

      if (isShortcut) {
        event.preventDefault()
        setSearchOpen(true)
      }

      if (event.key === 'Escape') {
        setSearchOpen(false)
      }
    }

    window.addEventListener('keydown', handleKeyDown)

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [])

  // Focus input and fetch incidents when modal opens
  useEffect(() => {
    if (!searchOpen) return

    inputRef.current?.focus()

    const fetchSearchData = async () => {
      try {
        setLoading(true)
        setError(null)

        const data = await getIncidents()

        setIncidents(data.results || [])
      } catch (err) {
        console.error('Global search failed:', err)
        setError('Unable to load incidents. Please try again.')
      } finally {
        setLoading(false)
      }
    }

    fetchSearchData()
  }, [searchOpen])

  // Filter incidents locally
  const filteredIncidents = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase()

    if (!normalizedQuery) return incidents.slice(0, 5)

    return incidents.filter((incident) => {
      const searchableFields = [
        incident.title,
        incident.service_name,
        incident.environment,
        incident.status,
        incident.id,
      ]

      return searchableFields.some((field) =>
        String(field || '').toLowerCase().includes(normalizedQuery)
      )
    })
  }, [incidents, query])

  const openIncident = (incidentId) => {
    setSearchOpen(false)
    setQuery('')
    navigate(`/incidents/${incidentId}`)
  }

  const closeSearch = () => {
    setSearchOpen(false)
    setQuery('')
  }

  return (
    <>
      <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-[#e5e5ea] bg-white/90 px-6 backdrop-blur-xl sm:px-8 lg:px-10">

        <div className="flex items-center gap-4">

          <button
            onClick={onMenuClick}
            className="rounded-lg p-2 text-[#6e6e73] transition hover:bg-[#f5f5f7]"
            aria-label="Open navigation menu"
          >
            <Menu size={21} />
          </button>

          <div>
            <p className="text-sm font-semibold tracking-tight text-[#1d1d1f]">
              Workspace
            </p>
            <p className="text-xs text-[#86868b]">
              Overview
            </p>
          </div>

        </div>

        <div className="flex items-center gap-5">

          {/* Global Search */}
          <button
            onClick={() => setSearchOpen(true)}
            className="hidden items-center gap-2 rounded-lg border border-[#e5e5ea] px-3 py-2 text-sm text-[#86868b] transition hover:border-[#c7c7cc] hover:bg-[#f5f5f7] sm:flex"
          >
            <Search size={16} />
            <span>Search</span>
            <span className="ml-3 rounded border border-[#e5e5ea] bg-[#f5f5f7] px-1.5 py-0.5 text-[10px] font-medium">
              ⌘ K
            </span>
          </button>

          <button
            className="rounded-lg p-2 text-[#86868b] transition hover:bg-[#f5f5f7]"
            aria-label="Notifications"
          >
            <Bell size={19} />
          </button>

          <button className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#e8f1fc] text-xs font-semibold text-[#0071e3]">
              U
            </div>

            <ChevronDown size={15} className="text-[#86868b]" />
          </button>

        </div>
      </header>

      {/* Global Search Modal */}
      {searchOpen && (
        <div
          className="fixed inset-0 z-[100] flex items-start justify-center bg-black/30 px-4 pt-[15vh] backdrop-blur-sm"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              closeSearch()
            }
          }}
        >
          <div className="search-modal">

            {/* Search Input */}
            <div className="flex items-center gap-3 border-b border-[#e5e5ea] px-5">

              <Search size={19} className="shrink-0 text-[#86868b]" />

              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search incidents, services..."
                className="h-16 min-w-0 flex-1 bg-transparent text-sm text-[#1d1d1f] outline-none placeholder:text-[#a1a1a6]"
              />

              <button
                onClick={closeSearch}
                className="rounded-md p-1.5 text-[#86868b] transition hover:bg-[#f5f5f7]"
                aria-label="Close search"
              >
                <X size={17} />
              </button>

            </div>

            {/* Results */}
            <div
              className="search-results"
            >

              <p className="px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-[#a1a1a6]">
                {query ? 'Search results' : 'Recent incidents'}
              </p>

              {loading && (
                <div className="flex items-center justify-center gap-2 py-12 text-sm text-[#86868b]">
                  <LoaderCircle size={17} className="animate-spin" />
                  Loading incidents...
                </div>
              )}

              {!loading && error && (
                <div className="flex items-center gap-2 px-3 py-8 text-sm text-[#d92d20]">
                  <AlertCircle size={17} />
                  {error}
                </div>
              )}

              {!loading && !error && filteredIncidents.length === 0 && (
                <div className="py-12 text-center">
                  <Search
                    size={22}
                    className="mx-auto mb-3 text-[#c7c7cc]"
                  />
                  <p className="text-sm font-medium text-[#1d1d1f]">
                    No incidents found
                  </p>
                  <p className="mt-1 text-xs text-[#86868b]">
                    Try another search term.
                  </p>
                </div>
              )}

              {!loading && !error && filteredIncidents.map((incident) => (
                <button
                  key={incident.id}
                  onClick={() => openIncident(incident.id)}
                  className="search-result"
                >
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[#fff0ef] text-[#ff3b30]">
                    <AlertCircle size={17} />
                  </div>

                  <div className="search-result-copy">

                    <p className="search-result-title">
                      {incident.title}
                    </p>

                    <p className="search-result-meta">
                      {incident.service_name} · {incident.environment}
                    </p>

                  </div>

                  <span className="shrink-0 rounded-md bg-[#f5f5f7] px-2 py-1 text-[10px] font-medium capitalize text-[#6e6e73]">
                    {incident.status}
                  </span>

                </button>
              ))}

            </div>

            {/* Footer */}
            <div className="flex items-center justify-between border-t border-[#e5e5ea] px-5 py-3 text-[11px] text-[#a1a1a6]">
              <span>Runtime RCA Search</span>

              <div className="flex items-center gap-3">
                <span>ESC to close</span>
                <span className="flex items-center gap-1">
                  <Command size={12} />
                  K
                </span>
              </div>
            </div>

          </div>
        </div>
      )}
    </>
  )
}

export default Navbar