import { StatsBar } from './StatsBar'

export function OshiAwardSlide({ slide, event }) {
  const { ign, trainee_name, uma_image, full_art_image, time, stats, quote } = slide
  const { track } = event
  const imageUrl = full_art_image ? `/${full_art_image}` : `/${uma_image}`

  return (
    <div class="slide oshi-award">
      <div class="slide-bg">
        <img src={imageUrl} alt="" draggable={false} />
      </div>
      <div class="slide-bg-overlay" />

      <div class="slide-content">
        <div class="slide-badges">
          <img class="badge-icon" src={`/${event.icon}`} alt={event.name} draggable={false} />
          <img class="badge-logo" src="/moologo2.png" alt="Moomoocows" draggable={false} />
        </div>

        <div class="slide-header">
          <div class="award-title">
            <svg class="trophy-icon" viewBox="0 0 24 24" fill="currentColor" width="28" height="28">
              <path d="M19 5h-2V3H7v2H5c-1.1 0-2 .9-2 2v1c0 2.55 1.92 4.63 4.39 4.94A5.01 5.01 0 0 0 11 15.9V19H7v2h10v-2h-4v-3.1a5.01 5.01 0 0 0 3.61-2.96C19.08 12.63 21 10.55 21 8V7c0-1.1-.9-2-2-2zM5 8V7h2v3.82C5.84 10.4 5 9.3 5 8zm14 0c0 1.3-.84 2.4-2 2.82V7h2v1z" />
            </svg>
            <span>OSHI'S CHAMPION AWARDEE</span>
          </div>
        </div>

        <div class={`slide-character${full_art_image ? ' full-art' : ''}`}>
          <img class="char-ghost" src={imageUrl} alt="" draggable={false} />
          <img class="char-main" src={imageUrl} alt={trainee_name} draggable={false} />
        </div>

        <div class="slide-info">
          <div class="subtitle">
            <span>THE ONLY</span>
            <span>{trainee_name.toUpperCase()}</span>
            <span>FINALS WINNER</span>
          </div>
          <div class="ign">{ign.toUpperCase()}</div>
          {quote && <div class="quote">"{quote}"</div>}
        </div>

        <div class="slide-footer">
          <div class="track-time">
            <span class="track-item">
              TRACK: {track.toUpperCase()}
            </span>
            <span class="track-item">
              <svg viewBox="0 0 24 24" fill="currentColor" width="32" height="32">
                <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm.5-13H11v6l5.2 3.2.8-1.3-4.5-2.7V7z" />
              </svg>
              TIME: {time}
            </span>
          </div>
          <StatsBar stats={stats} />
        </div>
      </div>
    </div>
  )
}
