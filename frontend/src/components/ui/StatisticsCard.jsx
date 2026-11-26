function StatisticsCard({ title, value, icon: Icon, color, description }) {
  return (
    <div className="stat-card">
      <div className="stat-card-top">
        <p className="stat-card-title">{title}</p>

        <div className={`stat-card-icon ${color}`}>
          <Icon size={19} strokeWidth={1.8} />
        </div>
      </div>

      <h2 className="stat-card-value">{value}</h2>

      <p className="stat-card-description">{description}</p>
    </div>
  )
}

export default StatisticsCard