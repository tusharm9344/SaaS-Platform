function StatisticsCard({ title, value, icon: Icon, color, description }) {
  return (
    <div className="min-w-0 rounded-2xl border border-[#e5e5ea] bg-white p-6 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-[0_8px_30px_rgba(0,0,0,0.04)]">

      <div className="flex items-center justify-between">
        <p className="text-[13px] font-medium text-[#86868b]">
          {title}
        </p>

        <div className={`rounded-xl p-2.5 ${color}`}>
          <Icon size={19} strokeWidth={1.8} />
        </div>
      </div>

      <h2 className="mt-6 text-[32px] font-semibold tracking-[-0.04em] text-[#1d1d1f]">
        {value}
      </h2>

      <p className="mt-2 text-xs leading-5 text-[#86868b]">
        {description}
      </p>

    </div>
  )
}

export default StatisticsCard