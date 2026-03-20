export function StatsBar({ stats }) {
  const entries = [
    { label: 'SPEED', value: stats.speed },
    { label: 'STAMINA', value: stats.stamina },
    { label: 'POWER', value: stats.power },
    { label: 'GUTS', value: stats.guts },
    { label: 'WIT', value: stats.wit },
  ]

  return (
    <div class="stats-bar">
      {entries.map((e) => (
        <div class="stat" key={e.label}>
          <span class="stat-value">{e.value}</span>
          <span class="stat-label">{e.label}</span>
        </div>
      ))}
    </div>
  )
}
