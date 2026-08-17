const STAT_CONFIG = [
  { key: 'speed',   label: 'Speed',   cls: 'speed' },
  { key: 'stamina', label: 'Stamina', cls: 'stamina' },
  { key: 'power',   label: 'Power',   cls: 'power' },
  { key: 'guts',    label: 'Guts',    cls: 'guts' },
  { key: 'wit',     label: 'Wit',     cls: 'wit' },
]

// Ceilings used to scale the bar fill, not to grade the stat. Decks through
// CM16 ran under the old scenario, where 1200 was the hard ceiling — scaling
// those against the current caps would render a maxed-out stat as a partial
// bar, so they keep the ceiling they were actually played under.
const LEGACY_CAPS   = { speed: 1200, stamina: 1200, power: 1200, guts: 1200, wit: 1200 }
const CURRENT_CAPS  = { speed: 1600, stamina: 1300, power: 1300, guts: 1500, wit: 1300 }
const CURRENT_CAPS_FROM_CM = 17

function capsForEvent(event) {
  const cm = Number(/^CM(\d+)$/i.exec(event?.id ?? '')?.[1])
  return cm >= CURRENT_CAPS_FROM_CM ? CURRENT_CAPS : LEGACY_CAPS
}

const base = import.meta.env.BASE_URL

// Mirrors uma-tools-1 HorseDef.tsx#rankForStat — canonical in-game tier
// indices for status-rank icons (ui_statusrank_NN.png).
function rankForStat(x) {
  if (x > 1200) {
    // Over-cap: the letter steps every 100 and the minor number every 10, so
    // each 100-point band occupies ten indices. Tops out at 97 (US9).
    return Math.min(18 + Math.floor((x - 1200) / 100) * 10 + Math.floor(x / 10) % 10, 97)
  }
  if (x >= 1150) return 17 // SS+
  if (x >= 1100) return 16 // SS
  if (x >= 400)  return 8 + Math.floor((x - 400) / 100)
  return Math.max(0, Math.floor(x / 50))
}

const RANK_LABELS = [
  'G', 'G+', 'F', 'F+', 'E', 'E+', 'D', 'D+',
  'C', 'C+', 'B', 'B+', 'A', 'A+', 'S', 'S+',
  'SS', 'SS+',
]

// Over-cap letters, one per 100-point band starting at 1200.
const OVER_CAP_LETTERS = ['UG', 'UF', 'UE', 'UD', 'UC', 'UB', 'UA', 'US']

function rankLabel(idx) {
  if (idx < RANK_LABELS.length) return RANK_LABELS[idx]
  const letter = OVER_CAP_LETTERS[Math.floor((idx - 18) / 10)]
  if (!letter) return '?'
  const minor = (idx - 18) % 10
  return minor ? `${letter}${minor}` : letter
}

function rankIconSrc(idx) {
  return `${base}statusrank/ui_statusrank_${String(idx).padStart(2, '0')}.png`
}

export function UmaStatsBar({ stats, event }) {
  const caps = capsForEvent(event)

  return (
    <div class="uma-stats-bar">
      {STAT_CONFIG.map(({ key, label, cls }) => {
        const val = stats?.[key] ?? 0
        const idx = rankForStat(val)
        const grade = rankLabel(idx)
        const pct = Math.min(val / caps[key], 1)

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
