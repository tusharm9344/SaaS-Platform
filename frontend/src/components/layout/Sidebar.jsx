import {
  LayoutDashboard,
  Layers,
  Server,
  AlertCircle,
  Settings,
  ChevronDown,
  Plus,
  X,
} from 'lucide-react'

const menuItems = [
  { name: 'Overview', icon: LayoutDashboard },
  { name: 'Applications', icon: Layers },
  { name: 'Services', icon: Server },
  { name: 'Incidents', icon: AlertCircle },
]

function Sidebar({ isOpen, onClose }) {
  return (
    <>
      {/* Background overlay */}
      <div
        onClick={onClose}
        className={`fixed inset-0 z-40 bg-black/20 backdrop-blur-[2px] transition-opacity duration-300 ${
          isOpen
            ? 'visible opacity-100'
            : 'invisible opacity-0'
        }`}
      />

      {/* Sidebar drawer */}
      <aside
        className={`fixed left-0 top-0 z-50 flex h-screen w-72 flex-col border-r border-[#e5e5ea] bg-white px-5 py-6 shadow-2xl transition-transform duration-300 ease-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >

        {/* Logo */}
        <div className="mb-10 flex items-center justify-between">
          <h1 className="text-[22px] font-semibold tracking-tight text-[#1d1d1f]">
            Runtime<span className="text-[#0071e3]">RCA</span>
          </h1>

          <button
            onClick={onClose}
            className="rounded-lg p-2 text-[#86868b] transition hover:bg-[#f5f5f7]"
          >
            <X size={19} />
          </button>
        </div>

        {/* Workspace */}
        <div className="mb-8 rounded-xl border border-[#e5e5ea] p-3">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#0071e3] text-sm font-semibold text-white">
              W
            </div>

            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-[#1d1d1f]">
                Workspace
              </p>
              <p className="text-xs text-[#86868b]">
                Free Plan
              </p>
            </div>

            <ChevronDown size={15} className="text-[#86868b]" />
          </div>
        </div>

        {/* Navigation */}
        <div>
          <p className="mb-3 px-3 text-[11px] font-semibold uppercase tracking-wider text-[#a1a1a6]">
            Workspace
          </p>

          <nav className="space-y-1">
            {menuItems.map((item, index) => {
              const Icon = item.icon
              const active = index === 0

              return (
                <button
                  key={item.name}
                  onClick={onClose}
                  className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-all ${
                    active
                      ? 'bg-[#f2f2f7] font-medium text-[#1d1d1f]'
                      : 'text-[#6e6e73] hover:bg-[#f5f5f7] hover:text-[#1d1d1f]'
                  }`}
                >
                  <Icon size={18} strokeWidth={1.8} />
                  {item.name}
                </button>
              )
            })}
          </nav>
        </div>

        {/* Bottom */}
        <div className="mt-auto space-y-2">
          <button
            onClick={onClose}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-[#6e6e73] transition hover:bg-[#f5f5f7]"
          >
            <Settings size={18} />
            Settings
          </button>

          <div className="border-t border-[#e5e5ea] pt-4">
            <button className="flex w-full items-center justify-center gap-2 rounded-lg bg-[#0071e3] px-4 py-2.5 text-sm font-medium text-white transition hover:bg-[#0077ed]">
              <Plus size={17} />
              New Application
            </button>
          </div>
        </div>

      </aside>
    </>
  )
}

export default Sidebar