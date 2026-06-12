import { getDisplayName } from '../../utils/names'
import { buildHash } from '../../utils/route'
import './styles.css'

const base = import.meta.env.BASE_URL

// Column count tuned to keep portraits legible: ~2 rows for typical decks,
// expanding to 3 rows past 18 so large fields (CM14 had 17) don't clip.
function gridColumns(n) {
  if (n <= 3) return 3
  if (n === 4) return 2
  if (n <= 6) return 3
  if (n <= 8) return 4
  if (n <= 10) return 5
  if (n <= 12) return 6
  if (n <= 14) return 7
  if (n <= 16) return 8
  return Math.ceil(n / (n > 18 ? 3 : 2))
}

export function TocSlide({ event, eventId, winners }) {
  const allTraineeNames = winners.map(w => w.trainee_name)
  const columns = gridColumns(winners.length)

  const goToWinner = (ign) => (e) => {
    e.stopPropagation()
    window.location.hash = buildHash(eventId, ign)
  }

  return (
    <div class="slide toc-slide">
      <div class="toc-glow toc-glow-orange" />
      <div class="toc-glow toc-glow-gold" />

      <div class="toc-content">
        <div class="toc-badges">
          <img src={`${base}${event.icon}`} alt={event.name} draggable={false} />
          <img src={`${base}moologo2.png`} alt="Moomoocows" draggable={false} />
        </div>

        <div class="toc-header">
          <div class="toc-eyebrow">OSHI'S CHAMPION AWARDEES</div>
          <div class="toc-title">{event.name}</div>
          <div class="toc-meta">
            <span>{event.track}</span>
            <span class="toc-meta-dot">•</span>
            <span>{winners.length} {winners.length === 1 ? 'WINNER' : 'WINNERS'}</span>
          </div>
        </div>

        <div class="toc-grid" style={{ '--toc-cols': columns }}>
          {winners.map((w) => {
            const displayName = getDisplayName(w.trainee_name, allTraineeNames)
            return (
              <div class="toc-card" key={w.ign} onClick={goToWinner(w.ign)} role="button" tabIndex={0}>
                <div class="toc-portrait">
                  <img
                    src={`${base}${w.uma_image}`}
                    alt={w.trainee_name}
                    draggable={false}
                  />
                </div>
                <div class="toc-card-info">
                  <div class="toc-ign" title={w.ign}>{w.ign}</div>
                  <div class="toc-uma" title={w.trainee_name}>{displayName}</div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
