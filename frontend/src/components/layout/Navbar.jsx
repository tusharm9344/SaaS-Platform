import {
  Search,
  Bell,
  ChevronDown,
  Menu,
} from 'lucide-react'

function Navbar({ onMenuClick }) {
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-[#e5e5ea] bg-white/90 px-6 sm:px-8 lg:px-10 backdrop-blur-xl">

      <div className="flex items-center gap-4">

        {/* Menu button */}
        <button
          onClick={onMenuClick}
          className="rounded-lg p-2 text-[#6e6e73] transition hover:bg-[#f5f5f7] hover:text-[#1d1d1f]"
          aria-label="Open navigation"
        >
          <Menu size={21} />
        </button>

        <div>
          <p className="text-sm font-medium text-[#e5e5ea]">
            Workspace
          </p>

          <h2 className="text-lg font-semibold tracking-tight text-[#1d1d1f]">
            Overview
          </h2>
        </div>

      </div>

      {/* Actions */}
      <div className="flex items-center gap-5">

        <button className="hidden items-center gap-2 rounded-lg border border-[#e5e5ea] px-3 py-2 text-sm text-[#86868b] transition hover:bg-[#f5f5f7] sm:flex">
          <Search size={16} />
          <span>Search</span>
          <span className="ml-4 rounded border border-[#e5e5ea] px-1.5 py-0.5 text-xs">
            ⌘ K
          </span>
        </button>

        <button className="relative rounded-lg p-2 text-[#6e6e73] transition hover:bg-[#f5f5f7]">
          <Bell size={19} />
          <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-[#ff3b30]" />
        </button>

        <div className="h-7 w-px bg-[#e5e5ea]" />

        <button className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#e8f1fc] text-sm font-semibold text-[#0071e3]">
            T
          </div>

          <ChevronDown size={15} className="text-[#86868b]" />
        </button>

      </div>
    </header>
  )
}

export default Navbar