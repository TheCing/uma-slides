import { useState, useEffect, useCallback, useRef, useMemo } from 'preact/hooks'
import { THEMES } from '../themes/registry'
import { TocSlide } from '../themes/toc/TocSlide'
import { findSlideIndex, buildHash } from '../utils/route'

export function SlideViewer({ slides, event, eventId, initialIgnSlug, onBack, onSlideChange }) {
  const allTraineeNames = useMemo(() => slides.map(s => s.trainee_name), [slides])
  const initialIndex = useMemo(() => findSlideIndex(slides, initialIgnSlug), [slides, initialIgnSlug])
  const [index, setIndex] = useState(initialIndex)
  const [displayIndex, setDisplayIndex] = useState(initialIndex)
  const [transitioning, setTransitioning] = useState(false)
  const [direction, setDirection] = useState(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [copied, setCopied] = useState(false)
  const stageRef = useRef(null)
  const total = slides.length

  // Push current slide IGN into the URL hash whenever it changes.
  useEffect(() => {
    if (onSlideChange && slides[displayIndex]) {
      onSlideChange(eventId, slides[displayIndex].ign)
    }
  }, [displayIndex, eventId, slides, onSlideChange])

  // Honor external hash changes (e.g. user edits the URL) by snapping index.
  useEffect(() => {
    const target = findSlideIndex(slides, initialIgnSlug)
    if (target !== index) {
      setIndex(target)
      setDisplayIndex(target)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialIgnSlug])

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

  const copyLink = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(window.location.href)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      /* clipboard blocked — silently noop */
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
  const isToc = slide?._layout === 'toc'
  const realWinners = useMemo(() => slides.filter(s => !s._layout), [slides])
  const SlideComponent = THEMES[event.theme] || THEMES['default']
  const transClass = transitioning ? `slide-exit slide-exit-${direction}` : 'slide-enter'

  return (
    <div class="slide-viewer" ref={stageRef}>
      <button
        class="copy-link-btn"
        onClick={copyLink}
        title="Copy link to this slide"
      >
        {copied ? (
          <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18">
            <path d="M9 16.17 4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18">
            <path d="M3.9 12c0-1.71 1.39-3.1 3.1-3.1h4V7H7a5 5 0 0 0 0 10h4v-1.9H7c-1.71 0-3.1-1.39-3.1-3.1zM8 13h8v-2H8v2zm9-6h-4v1.9h4c1.71 0 3.1 1.39 3.1 3.1s-1.39 3.1-3.1 3.1h-4V17h4a5 5 0 0 0 0-10z" />
          </svg>
        )}
      </button>
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
          {isToc ? (
            <TocSlide event={event} eventId={eventId} winners={realWinners} />
          ) : (
            <SlideComponent slide={slide} event={event} allTraineeNames={allTraineeNames} />
          )}
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
        <button
          class="nav-btn back-btn"
          onClick={() => { window.location.hash = buildHash(eventId) }}
          disabled={isToc}
          title="Back to summary"
        >
          <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
            <path d="M17.65 6.35A7.958 7.958 0 0 0 12 4a8 8 0 1 0 7.74 10h-2.08A6 6 0 1 1 12 6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z" />
          </svg>
        </button>
      </div>
    </div>
  )
}
