const STAT_CONFIG = [
  { key: 'speed',   label: 'Speed',   cls: 'speed' },
  { key: 'stamina', label: 'Stamina', cls: 'stamina' },
  { key: 'power',   label: 'Power',   cls: 'power' },
  { key: 'guts',    label: 'Guts',    cls: 'guts' },
  { key: 'wit',     label: 'Wit',     cls: 'wit' },
]

const base = import.meta.env.BASE_URL

// Mirrors uma-tools-1 HorseDef.tsx#rankForStat — canonical in-game tier
// indices for status-rank icons (ui_statusrank_NN.png).
function rankForStat(x) {
  if (x > 1200) {
    // Over-cap (with breakthroughs). Approximation; we only ever ship icons
    // through index 19, so anything higher clamps below.
    return Math.min(18 + Math.floor((x - 1200) / 100) * 10 + Math.floor(x / 10) % 10, 19)
  }
  if (x >= 1150) return 17 // SS+
  if (x >= 1100) return 16 // SS
  if (x >= 400)  return 8 + Math.floor((x - 400) / 100)
  return Math.max(0, Math.floor(x / 50))
}

const RANK_LABELS = [
  'G', 'G+', 'F', 'F+', 'E', 'E+', 'D', 'D+',
  'C', 'C+', 'B', 'B+', 'A', 'A+', 'S', 'S+',
  'SS', 'SS+', 'UG', 'UF',
]

function rankIconSrc(idx) {
  return `${base}statusrank/ui_statusrank_${String(idx).padStart(2, '0')}.png`
}

export function UmaStatsBar({ stats }) {
  const maxStat = 1200

  return (
    <div class="uma-stats-bar">
      {STAT_CONFIG.map(({ key, label, cls }) => {
        const val = stats?.[key] ?? 0
        const idx = rankForStat(val)
        const grade = RANK_LABELS[idx] ?? '?'
        const pct = Math.min(val / maxStat, 1)

        return (
          <div class="uma-stat" key={key}>
            <div class="uma-stat-header">
              <img
                class="uma-grade-icon"
                src={rankIconSrc(idx)}
                alt={grade}
                title={grade}
                draggable={false}
              />
              <span class="uma-stat-label">{label}</span>
            </div>
            <div class="uma-stat-bar-track">
              <div
                class={`uma-stat-bar-fill ${cls}`}
                style={{ width: `${pct * 100}%` }}
              />
            </div>
            <span class="uma-stat-value">{val.toLocaleString('en-US')}</span>
          </div>
        )
      })}
    </div>
  )
}
