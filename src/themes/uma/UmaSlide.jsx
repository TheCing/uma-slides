import { UmaStatsBar } from './UmaStatsBar'
import { getDisplayName } from '../../utils/names'
import './styles.css'

const base = import.meta.env.BASE_URL

function TrophySvg() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" width="22" height="22">
      <path d="M19 5h-2V3H7v2H5c-1.1 0-2 .9-2 2v1c0 2.55 1.92 4.63 4.39 4.94A5.01 5.01 0 0 0 11 15.9V19H7v2h10v-2h-4v-3.1a5.01 5.01 0 0 0 3.61-2.96C19.08 12.63 21 10.55 21 8V7c0-1.1-.9-2-2-2zM5 8V7h2v3.82C5.84 10.4 5 9.3 5 8zm14 0c0 1.3-.84 2.4-2 2.82V7h2v1z" />
    </svg>
  )
}

function ClockSvg() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" width="28" height="28">
      <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm.5-13H11v6l5.2 3.2.8-1.3-4.5-2.7V7z" />
    </svg>
  )
}

function MapPinSvg() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" width="28" height="28">
      <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5a2.5 2.5 0 0 1 0-5 2.5 2.5 0 0 1 0 5z" />
    </svg>
  )
}

const SPARKLE_POSITIONS = [
  { top: '8%', right: '12%', size: 12, delay: 0 },
  { top: '18%', right: '6%', size: 8, delay: 0.8 },
  { bottom: '25%', right: '15%', size: 10, delay: 1.6 },
  { top: '5%', left: '55%', size: 6, delay: 2.2 },
  { bottom: '15%', left: '48%', size: 9, delay: 0.4 },
]

function SparkleIcon({ size = 12 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
      <path
        d="M12 2L14.09 8.26L20 9.27L15.55 13.97L16.91 20L12 16.9L7.09 20L8.45 13.97L4 9.27L9.91 8.26L12 2Z"
        fill="#ffcd3c"
        opacity="0.7"
      />
    </svg>
  )
}

export function UmaSlide({ slide, event, allTraineeNames }) {
  const { ign, trainee_name, uma_image, full_art_image, full_art_compact, time, stats, quote } = slide
  const { track } = event
  const displayName = getDisplayName(trainee_name, allTraineeNames || [])
  const imageUrl = full_art_image ? `${base}${full_art_image}` : `${base}${uma_image}`
  const useFullArtLayout = !!full_art_image && !full_art_compact
  const smallFullArt = !!full_art_image && !!full_art_compact

  return (
    <div class="slide uma-slide">
      {/* Background glows */}
      <div class="uma-glow uma-glow-orange" />
      <div class="uma-glow uma-glow-pink" />
      <div class="uma-glow uma-glow-gold" />

      {/* Sparkles */}
      <div class="uma-sparkles">
        {SPARKLE_POSITIONS.map((pos, i) => (
          <div
            class="uma-sparkle"
            key={i}
            style={{
              ...pos,
              animationDelay: `${pos.delay}s`,
            }}
          >
            <SparkleIcon size={pos.size} />
          </div>
        ))}
      </div>

      {/* Content grid */}
      <div class="uma-content">
        {/* Badges */}
        <div class="uma-badges">
          <img src={`${base}${event.icon}`} alt={event.name} draggable={false} />
          <img src={`${base}moologo2.png`} alt="Moomoocows" draggable={false} />
        </div>

        {/* Ribbon header */}
        <div class="uma-header">
          <div class="uma-ribbon-wrapper">
            <div class="uma-ribbon-accent" />
            <div class="uma-ribbon-main">
              <div class="uma-ribbon-text">
                <TrophySvg />
                <span>OSHI'S CHAMPION AWARDEE</span>
              </div>
            </div>
          </div>
        </div>

        {/* Character */}
        <div class={`uma-character${useFullArtLayout ? ' full-art' : ''}${smallFullArt ? ' full-art-small' : ''}`}>
          <img class="char-ghost" src={imageUrl} alt="" draggable={false} />
          <img class="char-main" src={imageUrl} alt={trainee_name} draggable={false} />
        </div>

        {/* Info */}
        <div class="uma-info">
          <div class="uma-ign" style={{ fontSize: ign.length > 10 ? `clamp(28px, ${Math.max(3, 7 - (ign.length - 6) * 0.35)}vw, ${Math.max(50, 110 - (ign.length - 6) * 6)}px)` : undefined }}>{ign.toUpperCase()}</div>
          <div class="uma-subtitle">
            <span>THE ONLY</span>
            <span>{displayName.toUpperCase()}</span>
            <span>FINALS OSHI WINNER</span>
          </div>
          {quote && <div class="uma-quote">"{quote}"</div>}
        </div>

        {/* Footer */}
        <div class="uma-footer">
          <div class="uma-track-time">
            <span class="uma-track-item">
              EVENT: {event.name.toUpperCase()}
            </span>
            <span class="uma-track-item">
              <MapPinSvg />
              TRACK: {track.toUpperCase()}
            </span>
            <span class="uma-track-item">
              <ClockSvg />
              TIME: {time}
            </span>
          </div>
          <UmaStatsBar stats={stats} />
        </div>
      </div>
    </div>
  )
}
