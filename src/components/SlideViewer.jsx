import { useState, useEffect, useCallback, useRef, useMemo } from 'preact/hooks'
import { THEMES } from '../themes/registry'

export function SlideViewer({ slides, event, onBack }) {
  const allTraineeNames = useMemo(() => slides.map(s => s.trainee_name), [slides])
  const [index, setIndex] = useState(0)
  const [displayIndex, setDisplayIndex] = useState(0)
  const [transitioning, setTransitioning] = useState(false)
  const [direction, setDirection] = useState(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const stageRef = useRef(null)
  const total = slides.length

  const navigate = useCallback((newIndex, dir) => {
    if (transitioning || newIndex === index) return
    setDirection(dir)
    setTransitioning(true)
    setTimeout(() => {
      setDisplayIndex(newIndex)
      setIndex(newIndex)
      setTimeout(() => setTransitioning(false), 50)
    }, 300)
  }, [transitioning, index])

  const prev = useCallback(() => navigate(Math.max(0, index - 1), 'left'), [navigate, index])
  const next = useCallback(() => navigate(Math.min(total - 1, index + 1), 'right'), [navigate, index, total])

  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      stageRef.current?.requestFullscreen()
    } else {
      document.exitFullscreen()
    }
  }, [])

  useEffect(() => {
    const onFsChange = () => setIsFullscreen(!!document.fullscreenElement)
    document.addEventListener('fullscreenchange', onFsChange)
    return () => document.removeEventListener('fullscreenchange', onFsChange)
  }, [])

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'ArrowLeft') prev()
      else if (e.key === 'ArrowRight') next()
      else if (e.key === 'Escape' && isFullscreen) document.exitFullscreen()
      else if (e.key === 'f' || e.key === 'F') toggleFullscreen()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [prev, next, isFullscreen, toggleFullscreen])

  if (!slides.length) {
    return <div class="slide-viewer empty">No slides to display.</div>
  }

  const slide = slides[displayIndex]
  const SlideComponent = THEMES[event.theme] || THEMES['default']
  const transClass = transitioning ? `slide-exit slide-exit-${direction}` : 'slide-enter'

  return (
    <div class="slide-viewer" ref={stageRef}>
      <button class="fullscreen-btn" onClick={toggleFullscreen} title="Toggle fullscreen (F)">
        {isFullscreen ? (
          <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
            <path d="M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z" />
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
            <path d="M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z" />
          </svg>
        )}
      </button>
      <div class="slide-stage">
        <div class={`slide-transition ${transClass}`} key={displayIndex}>
          <SlideComponent slide={slide} event={event} allTraineeNames={allTraineeNames} />
        </div>
        <div class="slide-hit-prev" onClick={prev} />
        <div class="slide-hit-next" onClick={next} />
      </div>

      <div class="slide-controls">
        {onBack && (
          <button class="nav-btn back-btn" onClick={onBack} title="Back to event list">
            <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
              <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z" />
            </svg>
          </button>
        )}
        <button class="nav-btn" onClick={prev} disabled={index === 0}>
          <svg viewBox="0 0 24 24" fill="currentColor" width="24" height="24">
            <path d="M15.41 7.41 14 6l-6 6 6 6 1.41-1.41L10.83 12z" />
          </svg>
        </button>
        <span class="slide-counter">
          {index + 1} / {total}
        </span>
        <button
          class="nav-btn"
          onClick={next}
          disabled={index === total - 1}
        >
          <svg viewBox="0 0 24 24" fill="currentColor" width="24" height="24">
            <path d="M10 6 8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z" />
          </svg>
        </button>
      </div>
    </div>
  )
}
