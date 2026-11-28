import { useEffect, useState } from 'react'
import {
  Settings as SettingsIcon,
  BrainCircuit,
  ShieldCheck,
  LoaderCircle,
  CheckCircle2,
  AlertCircle,
  Eye,
  EyeOff,
  Save,
  Zap,
} from 'lucide-react'

import Sidebar from '../components/layout/Sidebar'
import Navbar from '../components/layout/Navbar'
import { getOrganizations } from '../services/applicationService'
import {
  getAIProviderConfig,
  saveAIProviderConfig,
  testAIProvider,
} from '../services/settingsService'

const providers = [
  { value: 'groq', label: 'Groq' },
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'gemini', label: 'Google Gemini' },
  { value: 'openrouter', label: 'OpenRouter' },
  { value: 'ollama', label: 'Ollama / Custom' },
]

function Settings() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [organizations, setOrganizations] = useState([])
  const [organizationId, setOrganizationId] = useState('')

  const [provider, setProvider] = useState('groq')
  const [modelName, setModelName] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [apiBase, setApiBase] = useState('')
  const [isEnabled, setIsEnabled] = useState(true)

  const [hasApiKey, setHasApiKey] = useState(false)
  const [configured, setConfigured] = useState(false)
  const [showKey, setShowKey] = useState(false)

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)

  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [testResult, setTestResult] = useState(null)

  useEffect(() => {
    const loadOrganizations = async () => {
      try {
        setLoading(true)

        const data = await getOrganizations()
        setOrganizations(data)

        if (data.length > 0) {
          setOrganizationId(data[0].id)
        } else {
          setError('No organization found for this account.')
        }
      } catch (err) {
        setError(
          err.response?.data?.detail ||
          'Unable to load organizations.'
        )
      } finally {
        setLoading(false)
      }
    }

    loadOrganizations()
  }, [])

  useEffect(() => {
    if (!organizationId) return

    const loadConfig = async () => {
      try {
        setLoading(true)
        setError('')
        setSuccess('')
        setTestResult(null)
        setApiKey('')

        const data = await getAIProviderConfig(organizationId)

        setConfigured(data.configured || false)

        if (data.configured) {
          setProvider(data.provider || 'groq')
          setModelName(data.model_name || '')
          setApiBase(data.api_base || '')
          setIsEnabled(data.is_enabled)
          setHasApiKey(data.has_api_key || false)
        } else {
          setProvider('groq')
          setModelName('')
          setApiBase('')
          setIsEnabled(true)
          setHasApiKey(false)
        }
      } catch (err) {
        setError(
          err.response?.data?.detail ||
          'Unable to load AI configuration.'
        )
      } finally {
        setLoading(false)
      }
    }

    loadConfig()
  }, [organizationId])

  const handleSave = async (event) => {
    event.preventDefault()

    setSaving(true)
    setError('')
    setSuccess('')
    setTestResult(null)

    try {
      const payload = {
        provider,
        model_name: modelName.trim(),
        api_base: apiBase.trim(),
        is_enabled: isEnabled,
      }

      if (apiKey.trim()) {
        payload.api_key = apiKey.trim()
      }

      const data = await saveAIProviderConfig(
        organizationId,
        payload
      )

      setConfigured(data.configured)
      setHasApiKey(data.has_api_key)
      setApiKey('')

      setSuccess('AI provider configuration saved successfully.')
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to save AI provider configuration.'
      )
    } finally {
      setSaving(false)
    }
  }

  const handleTest = async () => {
    setTesting(true)
    setError('')
    setSuccess('')
    setTestResult(null)

    try {
      const data = await testAIProvider(organizationId)

      setTestResult({
        success: true,
        message: data.response || 'Connection successful.',
      })
    } catch (err) {
      setTestResult({
        success: false,
        message:
          err.response?.data?.detail ||
          'Connection failed. Check your provider configuration.',
      })
    } finally {
      setTesting(false)
    }
  }

  const canManage = ['owner', 'admin'].includes(
    organizations.find((org) => org.id === organizationId)?.role
  )

  return (
    <div className="min-h-screen bg-[#f5f5f7]">
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <main className="min-h-screen">
        <Navbar onMenuClick={() => setSidebarOpen(true)} />

        <div className="page-container px-6 py-8">

          <div className="mb-8">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-blue-50 p-3">
                <SettingsIcon size={22} className="text-[#0071e3]" />
              </div>

              <div>
                <h1 className="text-2xl font-semibold text-[#1d1d1f]">
                  Settings
                </h1>

                <p className="mt-1 text-sm text-[#86868b]">
                  Manage your workspace and AI investigation configuration.
                </p>
              </div>
            </div>
          </div>

          {error && (
            <div className="mb-5 flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              <AlertCircle size={17} />
              {error}
            </div>
          )}

          {success && (
            <div className="mb-5 flex items-center gap-2 rounded-xl border border-green-200 bg-green-50 p-4 text-sm text-green-700">
              <CheckCircle2 size={17} />
              {success}
            </div>
          )}

          {loading ? (
            <div className="flex items-center justify-center rounded-2xl border border-[#e5e5ea] bg-white py-20">
              <LoaderCircle className="animate-spin text-[#0071e3]" />
              <span className="ml-3 text-sm text-[#86868b]">
                Loading settings...
              </span>
            </div>
          ) : (
            <div className="max-w-4xl space-y-6">

              {/* Organization */}
              <section className="rounded-2xl border border-[#e5e5ea] bg-white p-6">
                <h2 className="font-semibold text-[#1d1d1f]">
                  Workspace
                </h2>

                <p className="mt-1 text-sm text-[#86868b]">
                  Select the organization whose settings you want to manage.
                </p>

                <div className="mt-5 max-w-md">
                  <label className="mb-2 block text-sm font-medium text-[#1d1d1f]">
                    Organization
                  </label>

                  <select
                    value={organizationId}
                    onChange={(e) => setOrganizationId(e.target.value)}
                    className="w-full rounded-lg border border-[#d2d2d7] bg-white px-3 py-2.5 text-sm outline-none focus:border-[#0071e3]"
                  >
                    {organizations.map((org) => (
                      <option key={org.id} value={org.id}>
                        {org.name}
                      </option>
                    ))}
                  </select>
                </div>
              </section>

              {/* AI Configuration */}
              <section className="rounded-2xl border border-[#e5e5ea] bg-white p-6">

                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3">
                    <div className="rounded-xl bg-purple-50 p-3">
                      <BrainCircuit
                        size={22}
                        className="text-purple-600"
                      />
                    </div>

                    <div>
                      <h2 className="font-semibold text-[#1d1d1f]">
                        AI Investigation Provider
                      </h2>

                      <p className="mt-1 text-sm text-[#86868b]">
                        Configure the AI provider used for root-cause analysis.
                      </p>
                    </div>
                  </div>

                  <span className={`rounded-full px-3 py-1 text-xs font-medium ${
                    configured && hasApiKey
                      ? 'bg-green-50 text-green-700'
                      : 'bg-gray-100 text-gray-600'
                  }`}>
                    {configured && hasApiKey ? 'Configured' : 'Not configured'}
                  </span>
                </div>

                <form onSubmit={handleSave} className="mt-7 space-y-5">

                  <div>
                    <label className="mb-2 block text-sm font-medium text-[#1d1d1f]">
                      AI Provider
                    </label>

                    <select
                      value={provider}
                      onChange={(e) => setProvider(e.target.value)}
                      disabled={!canManage}
                      className="w-full rounded-lg border border-[#d2d2d7] bg-white px-3 py-2.5 text-sm outline-none focus:border-[#0071e3] disabled:bg-gray-100"
                    >
                      {providers.map((item) => (
                        <option key={item.value} value={item.value}>
                          {item.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="mb-2 block text-sm font-medium text-[#1d1d1f]">
                      Model Name
                    </label>

                    <input
                      type="text"
                      value={modelName}
                      onChange={(e) => setModelName(e.target.value)}
                      placeholder="e.g. groq/openai/gpt-oss-120b"
                      required
                      disabled={!canManage}
                      className="w-full rounded-lg border border-[#d2d2d7] px-3 py-2.5 text-sm outline-none focus:border-[#0071e3] disabled:bg-gray-100"
                    />

                    <p className="mt-1.5 text-xs text-[#86868b]">
                      Enter the model identifier supported by your provider and LiteLLM.
                    </p>
                  </div>

                  <div>
                    <label className="mb-2 block text-sm font-medium text-[#1d1d1f]">
                      API Key
                    </label>

                    <div className="relative">
                      <input
                        type={showKey ? 'text' : 'password'}
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                        placeholder={
                          hasApiKey
                            ? 'Saved securely. Enter a new key to replace it.'
                            : 'Enter your provider API key'
                        }
                        disabled={!canManage}
                        className="w-full rounded-lg border border-[#d2d2d7] px-3 py-2.5 pr-11 text-sm outline-none focus:border-[#0071e3] disabled:bg-gray-100"
                      />

                      <button
                        type="button"
                        onClick={() => setShowKey(!showKey)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-[#86868b]"
                        aria-label={showKey ? 'Hide API key' : 'Show API key'}
                      >
                        {showKey ? <EyeOff size={17} /> : <Eye size={17} />}
                      </button>
                    </div>

                    <p className="mt-1.5 flex items-center gap-1 text-xs text-[#86868b]">
                      <ShieldCheck size={13} />
                      API keys are encrypted before being stored.
                    </p>
                  </div>

                  <div>
                    <label className="mb-2 block text-sm font-medium text-[#1d1d1f]">
                      Custom API Base URL
                      <span className="ml-2 font-normal text-[#86868b]">
                        (Optional)
                      </span>
                    </label>

                    <input
                      type="url"
                      value={apiBase}
                      onChange={(e) => setApiBase(e.target.value)}
                      placeholder="https://api.example.com/v1"
                      disabled={!canManage}
                      className="w-full rounded-lg border border-[#d2d2d7] px-3 py-2.5 text-sm outline-none focus:border-[#0071e3] disabled:bg-gray-100"
                    />
                  </div>

                  <div className="flex items-center justify-between rounded-xl border border-[#e5e5ea] bg-[#fafafa] p-4">
                    <div>
                      <p className="text-sm font-medium text-[#1d1d1f]">
                        Enable AI Investigations
                      </p>

                      <p className="mt-1 text-xs text-[#86868b]">
                        Allow RuntimeRCA to use this provider for investigations.
                      </p>
                    </div>

                    <button
                      type="button"
                      role="switch"
                      aria-checked={isEnabled}
                      disabled={!canManage}
                      onClick={() => setIsEnabled(!isEnabled)}
                      className={`relative h-6 w-11 rounded-full transition ${
                        isEnabled ? 'bg-[#0071e3]' : 'bg-gray-300'
                      } disabled:opacity-50`}
                    >
                      <span
                        className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition ${
                          isEnabled ? 'left-[22px]' : 'left-0.5'
                        }`}
                      />
                    </button>
                  </div>

                  {!canManage && (
                    <p className="text-sm text-amber-700">
                      Only organization owners and admins can change AI settings.
                    </p>
                  )}

                  <div className="flex flex-wrap items-center gap-3 border-t border-[#e5e5ea] pt-5">

                    <button
                      type="submit"
                      disabled={saving || !canManage}
                      className="flex items-center gap-2 rounded-lg bg-[#0071e3] px-5 py-2.5 text-sm font-medium text-white transition hover:bg-[#0077ed] disabled:opacity-50"
                    >
                      {saving ? (
                        <LoaderCircle size={16} className="animate-spin" />
                      ) : (
                        <Save size={16} />
                      )}

                      {saving ? 'Saving...' : 'Save Configuration'}
                    </button>

                    <button
                      type="button"
                      onClick={handleTest}
                      disabled={testing || !configured || !hasApiKey || !canManage || !isEnabled}
                      className="flex items-center gap-2 rounded-lg border border-[#d2d2d7] bg-white px-5 py-2.5 text-sm font-medium text-[#1d1d1f] transition hover:bg-[#f5f5f7] disabled:opacity-50"
                    >
                      {testing ? (
                        <LoaderCircle size={16} className="animate-spin" />
                      ) : (
                        <Zap size={16} />
                      )}

                      {testing ? 'Testing...' : 'Test Connection'}
                    </button>
                  </div>
                </form>

                {testResult && (
                  <div className={`mt-5 flex items-start gap-2 rounded-xl border p-4 text-sm ${
                    testResult.success
                      ? 'border-green-200 bg-green-50 text-green-700'
                      : 'border-red-200 bg-red-50 text-red-700'
                  }`}>
                    {testResult.success ? (
                      <CheckCircle2 size={18} className="mt-0.5 shrink-0" />
                    ) : (
                      <AlertCircle size={18} className="mt-0.5 shrink-0" />
                    )}

                    <div>
                      <p className="font-medium">
                        {testResult.success
                          ? 'Connection successful'
                          : 'Connection failed'}
                      </p>

                      <p className="mt-1">
                        {testResult.message}
                      </p>
                    </div>
                  </div>
                )}
              </section>

              {/* Security information */}
              <section className="flex items-start gap-3 rounded-2xl border border-blue-100 bg-blue-50 p-5">
                <ShieldCheck
                  size={21}
                  className="mt-0.5 shrink-0 text-[#0071e3]"
                />

                <div>
                  <p className="text-sm font-semibold text-[#1d1d1f]">
                    Your credentials stay protected
                  </p>

                  <p className="mt-1 text-sm leading-relaxed text-[#6e6e73]">
                    RuntimeRCA encrypts provider API keys before storing them.
                    Your existing key is never returned to the frontend.
                    You can replace it at any time by entering a new key.
                  </p>
                </div>
              </section>

            </div>
          )}
        </div>
      </main>
    </div>
  )
}

export default Settings