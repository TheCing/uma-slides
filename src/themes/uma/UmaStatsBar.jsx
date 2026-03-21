const STAT_CONFIG = [
  { key: 'speed',   label: 'Speed',   cls: 'speed' },
  { key: 'stamina', label: 'Stamina', cls: 'stamina' },
  { key: 'power',   label: 'Power',   cls: 'power' },
  { key: 'guts',    label: 'Guts',    cls: 'guts' },
  { key: 'wit',     label: 'Wit',     cls: 'wit' },
]

function getGrade(value) {
  if (value >= 1200) return 'S'
  if (value >= 1100) return 'A+'
  if (value >= 1000) return 'A'
  if (value >= 900)  return 'B+'
  if (value >= 800)  return 'B'
  if (value >= 700)  return 'C+'
  if (value >= 600)  return 'C'
  if (value >= 500)  return 'D+'
  if (value >= 400)  return 'D'
  if (value >= 300)  return 'E+'
  if (value >= 200)  return 'E'
  if (value >= 150)  return 'F+'
  if (value >= 100)  return 'F'
  if (value >= 50)   return 'G+'
  return 'G'
}

function gradeBase(grade) {
  return grade.replace('+', '')
}

export function UmaStatsBar({ stats }) {
  const maxStat = 1200

  return (
    <div class="uma-stats-bar">
      {STAT_CONFIG.map(({ key, label, cls }) => {
        const val = stats?.[key] ?? 0
        const grade = getGrade(val)
        const pct = Math.min(val / maxStat, 1)

        return (
          <div class="uma-stat" key={key}>
            <div class="uma-stat-header">
              <span class={`uma-grade uma-grade-${gradeBase(grade)}`}>{grade}</span>
              <span class="uma-stat-label">{label}</span>
            </div>
            <div class="uma-stat-bar-track">
              <div
                class={`uma-stat-bar-fill ${cls}`}
                style={{ width: `${pct * 100}%` }}
              />
            </div>
            <span class="uma-stat-value">{val}</span>
          </div>
        )
      })}
    </div>
  )
}
