import { useCallback, useEffect, useState } from 'react'
import {
  Plus,
  Layers,
  KeyRound,
  Copy,
  Check,
  Trash2,
  X,
  RefreshCw,
  Search,
  Activity,
  ShieldCheck,
} from 'lucide-react'

import Sidebar from '../components/layout/Sidebar'
import Navbar from '../components/layout/Navbar'

import {
  getOrganizations,
  getApplications,
  createApplication,
  updateApplication,
  getApplicationKeys,
  createApplicationKey,
  revokeApplicationKey,
} from '../services/applicationService'

function Applications() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [applications, setApplications] = useState([])
  const [organizations, setOrganizations] = useState([])
  const [selectedApplication, setSelectedApplication] = useState(null)
  const [keys, setKeys] = useState([])
  const [search, setSearch] = useState('')

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionLoading, setActionLoading] = useState(false)

  const [showCreate, setShowCreate] = useState(false)
  const [showKeys, setShowKeys] = useState(false)
  const [newRawKey, setNewRawKey] = useState('')
  const [copied, setCopied] = useState(false)

  const [form, setForm] = useState({
    name: '',
    slug: '',
    description: '',
    organization_id: '',
  })

  const loadData = useCallback(async () => {
    try {
      setError('')

      const [orgs, apps] = await Promise.all([
        getOrganizations(),
        getApplications(),
      ])

      setOrganizations(orgs)
      setApplications(apps)

      setForm((previous) => ({
        ...previous,
        organization_id:
          previous.organization_id || orgs[0]?.id || '',
      }))
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to load applications. Check your connection and authentication.'
      )
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  const filteredApplications = applications.filter((app) =>
    `${app.name} ${app.slug} ${app.organization_name}`
      .toLowerCase()
      .includes(search.toLowerCase())
  )

  const handleCreate = async (event) => {
    event.preventDefault()

    if (!form.organization_id) {
      setError('Select an organization first.')
      return
    }

    try {
      setActionLoading(true)
      setError('')

      await createApplication({
        name: form.name,
        slug: form.slug,
        description: form.description,
        organization_id: form.organization_id,
      })

      setShowCreate(false)
      setForm((previous) => ({
        ...previous,
        name: '',
        slug: '',
        description: '',
      }))

      await loadData()
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        JSON.stringify(err.response?.data || 'Application creation failed.')
      )
    } finally {
      setActionLoading(false)
    }
  }

  const openKeys = async (application) => {
    setSelectedApplication(application)
    setShowKeys(true)
    setNewRawKey('')
    setKeys([])

    try {
      const data = await getApplicationKeys(application.id)
      setKeys(data)
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Unable to load API keys.'
      )
    }
  }

  const handleGenerateKey = async () => {
    const name = window.prompt('Enter a name for this API key:')

    if (!name?.trim()) return

    try {
      setActionLoading(true)

      const result = await createApplicationKey(
        selectedApplication.id,
        name.trim()
      )

      setNewRawKey(result.raw_key)

      const updatedKeys = await getApplicationKeys(
        selectedApplication.id
      )

      setKeys(updatedKeys)
      await loadData()
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Unable to generate API key.'
      )
    } finally {
      setActionLoading(false)
    }
  }

  const handleRevoke = async (keyId) => {
    if (!window.confirm('Are you sure you want to revoke this API key?')) {
      return
    }

    try {
      setActionLoading(true)

      await revokeApplicationKey(
        selectedApplication.id,
        keyId
      )

      setKeys(await getApplicationKeys(selectedApplication.id))
      await loadData()
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Unable to revoke API key.'
      )
    } finally {
      setActionLoading(false)
    }
  }

  const handleToggleStatus = async (application) => {
    try {
      await updateApplication(application.id, {
        is_active: !application.is_active,
      })

      await loadData()
    } catch (err) {
      setError(
        err.response?.data?.detail || 'Unable to update application.'
      )
    }
  }

  const copyKey = async () => {
    try {
      await navigator.clipboard.writeText(newRawKey)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      setError('Unable to access clipboard. Copy the key manually.')
    }
  }

  return (
    <div className="min-h-screen bg-[#f5f5f7]">
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="min-h-screen lg:pl-72">
        <Navbar onMenuClick={() => setSidebarOpen(true)} />

        <main className="mx-auto max-w-7xl px-5 py-8 sm:px-8">
          <div className="mb-8 flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
            <div>
              <h1 className="text-2xl font-semibold tracking-tight text-[#1d1d1f]">
                Applications
              </h1>
              <p className="mt-1 text-sm text-[#86868b]">
                Manage your applications and their ingestion credentials.
              </p>
            </div>

            <button
              onClick={() => setShowCreate(true)}
              className="flex items-center justify-center gap-2 rounded-xl bg-[#0071e3] px-4 py-2.5 text-sm font-medium text-white transition hover:bg-[#0077ed]"
            >
              <Plus size={17} />
              New Application
            </button>
          </div>

          {error && (
            <div className="mb-5 flex items-center justify-between rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              <span>{error}</span>
              <button onClick={() => setError('')}>
                <X size={17} />
              </button>
            </div>
          )}

          <div className="mb-6 grid gap-4 sm:grid-cols-3">
            <StatCard
              label="Total Applications"
              value={applications.length}
              icon={Layers}
            />
            <StatCard
              label="Active Applications"
              value={applications.filter((a) => a.is_active).length}
              icon={Activity}
            />
            <StatCard
              label="Connected Services"
              value={applications.reduce(
                (total, app) => total + (app.services_count || 0),
                0
              )}
              icon={ShieldCheck}
            />
          </div>

          <div className="rounded-2xl border border-[#e5e5ea] bg-white">
            <div className="flex flex-col justify-between gap-4 border-b border-[#e5e5ea] p-5 sm:flex-row sm:items-center">
              <div>
                <h2 className="font-semibold text-[#1d1d1f]">
                  Registered Applications
                </h2>
                <p className="mt-1 text-xs text-[#86868b]">
                  Applications registered with RuntimeRCA.
                </p>
              </div>

              <div className="relative">
                <Search
                  size={16}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-[#86868b]"
                />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search applications..."
                  className="w-full rounded-lg border border-[#e5e5ea] py-2 pl-9 pr-3 text-sm outline-none focus:border-[#0071e3] sm:w-64"
                />
              </div>
            </div>

            {loading ? (
              <div className="p-12 text-center text-sm text-[#86868b]">
                Loading applications...
              </div>
            ) : filteredApplications.length === 0 ? (
              <div className="p-12 text-center">
                <Layers
                  size={32}
                  className="mx-auto mb-3 text-[#a1a1a6]"
                />
                <p className="font-medium text-[#1d1d1f]">
                  No applications found
                </p>
                <p className="mt-1 text-sm text-[#86868b]">
                  Register your first application to get started.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-[#fafafa] text-xs text-[#86868b]">
                    <tr>
                      <th className="px-5 py-4 font-medium">Application</th>
                      <th className="px-5 py-4 font-medium">Organization</th>
                      <th className="px-5 py-4 font-medium">Services</th>
                      <th className="px-5 py-4 font-medium">API Keys</th>
                      <th className="px-5 py-4 font-medium">Status</th>
                      <th className="px-5 py-4 text-right font-medium">Actions</th>
                    </tr>
                  </thead>

                  <tbody className="divide-y divide-[#f0f0f2]">
                    {filteredApplications.map((app) => (
                      <tr key={app.id} className="hover:bg-[#fafafa]">
                        <td className="px-5 py-4">
                          <p className="font-medium text-[#1d1d1f]">
                            {app.name}
                          </p>
                          <p className="mt-1 text-xs text-[#86868b]">
                            {app.slug}
                          </p>
                        </td>

                        <td className="px-5 py-4 text-[#6e6e73]">
                          {app.organization_name}
                        </td>

                        <td className="px-5 py-4 text-[#6e6e73]">
                          {app.services_count}
                        </td>

                        <td className="px-5 py-4 text-[#6e6e73]">
                          {app.active_api_keys_count}
                        </td>

                        <td className="px-5 py-4">
                          <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                            app.is_active
                              ? 'bg-green-50 text-green-700'
                              : 'bg-gray-100 text-gray-600'
                          }`}>
                            {app.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>

                        <td className="px-5 py-4">
                          <div className="flex justify-end gap-2">
                            <button
                              onClick={() => openKeys(app)}
                              title="Manage API keys"
                              className="rounded-lg border border-[#e5e5ea] p-2 text-[#6e6e73] hover:bg-[#f5f5f7]"
                            >
                              <KeyRound size={16} />
                            </button>

                            <button
                              onClick={() => handleToggleStatus(app)}
                              title={app.is_active ? 'Deactivate' : 'Activate'}
                              className="rounded-lg border border-[#e5e5ea] p-2 text-[#6e6e73] hover:bg-[#f5f5f7]"
                            >
                              <RefreshCw size={16} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </main>
      </div>

      {showCreate && (
        <Modal title="Register Application" onClose={() => setShowCreate(false)}>
          <form onSubmit={handleCreate} className="space-y-4">
            <Field
              label="Application name"
              value={form.name}
              onChange={(value) => setForm({ ...form, name: value })}
              placeholder="e.g. Payment API"
              required
            />

            <Field
              label="Slug (optional)"
              value={form.slug}
              onChange={(value) => setForm({ ...form, slug: value })}
              placeholder="payment-api"
            />

            <div>
              <label className="mb-1.5 block text-sm font-medium text-[#1d1d1f]">
                Organization
              </label>

              <select
                required
                value={form.organization_id}
                onChange={(e) => setForm({
                  ...form,
                  organization_id: e.target.value,
                })}
                className="w-full rounded-lg border border-[#e5e5ea] px-3 py-2.5 text-sm outline-none focus:border-[#0071e3]"
              >
                <option value="">Select organization</option>
                {organizations.map((org) => (
                  <option key={org.id} value={org.id}>
                    {org.name} ({org.role})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="mb-1.5 block text-sm font-medium text-[#1d1d1f]">
                Description
              </label>
              <textarea
                rows={3}
                value={form.description}
                onChange={(e) => setForm({
                  ...form,
                  description: e.target.value,
                })}
                className="w-full rounded-lg border border-[#e5e5ea] px-3 py-2.5 text-sm outline-none focus:border-[#0071e3]"
                placeholder="What does this application do?"
              />
            </div>

            <div className="flex justify-end gap-3 pt-3">
              <button
                type="button"
                onClick={() => setShowCreate(false)}
                className="rounded-lg border border-[#e5e5ea] px-4 py-2 text-sm"
              >
                Cancel
              </button>

              <button
                disabled={actionLoading || !organizations.length}
                className="rounded-lg bg-[#0071e3] px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
              >
                {actionLoading ? 'Creating...' : 'Create Application'}
              </button>
            </div>
          </form>
        </Modal>
      )}

      {showKeys && selectedApplication && (
        <Modal
          title={`API Keys · ${selectedApplication.name}`}
          onClose={() => {
            setShowKeys(false)
            setNewRawKey('')
          }}
        >
          <div className="space-y-5">
            {newRawKey && (
              <div className="rounded-xl border border-green-200 bg-green-50 p-4">
                <p className="mb-2 text-sm font-semibold text-green-800">
                  API key generated successfully
                </p>

                <p className="mb-3 text-xs text-green-700">
                  Copy this key now. It cannot be retrieved again.
                </p>

                <div className="flex gap-2">
                  <input
                    readOnly
                    value={newRawKey}
                    className="min-w-0 flex-1 rounded-lg border border-green-200 bg-white px-3 py-2 text-xs"
                  />

                  <button
                    onClick={copyKey}
                    className="rounded-lg bg-green-700 px-3 text-white"
                  >
                    {copied ? <Check size={17} /> : <Copy size={17} />}
                  </button>
                </div>
              </div>
            )}

            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-[#1d1d1f]">
                  Application credentials
                </p>
                <p className="text-xs text-[#86868b]">
                  Manage ingestion API keys.
                </p>
              </div>

              <button
                disabled={actionLoading || !selectedApplication.is_active}
                onClick={handleGenerateKey}
                className="flex items-center gap-2 rounded-lg bg-[#0071e3] px-3 py-2 text-xs font-medium text-white disabled:opacity-50"
              >
                <Plus size={15} />
                Generate key
              </button>
            </div>

            {keys.length === 0 ? (
              <p className="rounded-lg bg-[#f5f5f7] p-5 text-center text-sm text-[#86868b]">
                No API keys registered.
              </p>
            ) : (
              <div className="space-y-3">
                {keys.map((key) => (
                  <div
                    key={key.id}
                    className="flex items-center justify-between gap-3 rounded-xl border border-[#e5e5ea] p-4"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-[#1d1d1f]">
                        {key.name}
                      </p>
                      <p className="mt-1 font-mono text-xs text-[#86868b]">
                        {key.key_prefix}••••••
                      </p>
                      <p className="mt-1 text-xs text-[#86868b]">
                        {key.is_active ? 'Active' : 'Revoked'}
                      </p>
                    </div>

                    {key.is_active && (
                      <button
                        disabled={actionLoading}
                        onClick={() => handleRevoke(key.id)}
                        title="Revoke key"
                        className="rounded-lg p-2 text-red-500 hover:bg-red-50"
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  )
}

function StatCard({ label, value, icon: Icon }) {
  return (
    <div className="rounded-2xl border border-[#e5e5ea] bg-white p-5">
      <div className="flex items-center justify-between">
        <p className="text-sm text-[#86868b]">{label}</p>
        <Icon size={19} className="text-[#0071e3]" />
      </div>
      <p className="mt-3 text-2xl font-semibold text-[#1d1d1f]">
        {value}
      </p>
    </div>
  )
}

function Modal({ title, onClose, children }) {
  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 p-4">
      <div className="max-h-[90vh] w-full max-w-xl overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-[#1d1d1f]">
            {title}
          </h2>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-[#86868b] hover:bg-[#f5f5f7]"
          >
            <X size={18} />
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}

function Field({ label, value, onChange, placeholder, required }) {
  return (
    <div>
      <label className="mb-1.5 block text-sm font-medium text-[#1d1d1f]">
        {label}
      </label>
      <input
        required={required}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-lg border border-[#e5e5ea] px-3 py-2.5 text-sm outline-none focus:border-[#0071e3]"
      />
    </div>
  )
}

export default Applications