import { useState, useEffect, useCallback, useRef, useMemo } from 'preact/hooks'
import { THEMES } from '../themes/registry'
import { TocSlide } from '../themes/toc/TocSlide'
import { findSlideIndex, buildHash } from '../utils/route'

const discordEnabled = import.meta.env.DEV && !!import.meta.env.VITE_DISCORD_WEBHOOK_URL

export function SlideViewer({ slides, event, eventId, initialIgnSlug, onBack, onSlideChange }) {
  const allTraineeNames = useMemo(() => slides.map(s => s.trainee_name), [slides])
  const initialIndex = useMemo(() => findSlideIndex(slides, initialIgnSlug), [slides, initialIgnSlug])
  const [index, setIndex] = useState(initialIndex)
  const [displayIndex, setDisplayIndex] = useState(initialIndex)
  const [transitioning, setTransitioning] = useState(false)
  const [direction, setDirection] = useState(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [copied, setCopied] = useState(false)
  const [postState, setPostState] = useState({ status: 'idle', progress: null })
  const stageRef = useRef(null)
  const slideStageRef = useRef(null)
  const total = slides.length
  const discordOn = discordEnabled

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

  const postCurrent = useCallback(async () => {
    if (!discordOn || postState.status !== 'idle') return
    const target = slideStageRef.current
    if (!target) return
    setPostState({ status: 'busy', progress: { phase: 'posting', i: 0, total: 1 } })
    try {
      const { postSlide } = await import('../lib/discord')
      await postSlide({ slide: slides[displayIndex], event, stageEl: target })
      setPostState({ status: 'success', progress: null })
    } catch (e) {
      console.error('[discord] post failed', e)
      setPostState({ status: 'error', progress: null, message: String(e?.message || e) })
    }
    setTimeout(() => setPostState({ status: 'idle', progress: null }), 2500)
  }, [discordOn, postState.status, slides, displayIndex, event])

  const postAll = useCallback(async () => {
    if (!discordOn || postState.status !== 'idle') return
    const realSlides = slides.filter((s) => !s._layout)
    if (!realSlides.length) return
    if (!window.confirm(`Post all ${realSlides.length} awards to Discord as separate forum threads?`)) return
    setPostState({ status: 'busy', progress: { phase: 'capturing', i: 0, total: realSlides.length } })
    const { postAllSlides, captureSlide } = await import('../lib/discord')
    const captureFor = async (slide) => {
      const targetIndex = slides.findIndex((s) => s.ign === slide.ign && !s._layout)
      setDisplayIndex(targetIndex)
      setIndex(targetIndex)
      await new Promise((r) => setTimeout(r, 700))
      return captureSlide(slideStageRef.current)
    }
    try {
      const results = await postAllSlides({
        slides: realSlides,
        event,
        captureFor,
        onProgress: (p) => setPostState({ status: 'busy', progress: p }),
      })
      const failed = results.filter((r) => !r.ok)
      if (failed.length) {
        console.warn('[discord] some posts failed', failed)
        setPostState({ status: 'error', progress: null, message: `${failed.length}/${results.length} failed` })
      } else {
        setPostState({ status: 'success', progress: null, message: `${results.length} posted` })
      }
    } catch (e) {
      console.error('[discord] bulk post failed', e)
      setPostState({ status: 'error', progress: null, message: String(e?.message || e) })
    }
    setTimeout(() => setPostState({ status: 'idle', progress: null }), 4000)
  }, [discordOn, postState.status, slides, event])

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
      <div class="slide-stage" ref={slideStageRef}>
        <div class={`slide-transition ${transClass}`} key={displayIndex}>
          {isToc ? (
            <TocSlide
              event={event}
              eventId={eventId}
              winners={slide._tocWinners || realWinners}
              totalWinners={realWinners.length}
              page={slide._tocPage || 0}
              pages={slide._tocPages || 1}
            />
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
        {discordOn && !isToc && (
          <button
            class={`nav-btn discord-btn discord-${postState.status}`}
            onClick={postCurrent}
            disabled={postState.status !== 'idle'}
            title="Post this slide to Discord"
          >
            {postState.status === 'busy' ? (
              <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20" class="spin">
                <path d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46A7.93 7.93 0 0 0 20 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74A7.93 7.93 0 0 0 4 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z" />
              </svg>
            ) : postState.status === 'success' ? (
              <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                <path d="M9 16.17 4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
              </svg>
            ) : (
              <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                <path d="M19.54 0c1.356 0 2.46 1.104 2.46 2.472v21.528l-2.58-2.28-1.452-1.344-1.536-1.428.636 2.22H3.46c-1.356 0-2.46-1.104-2.46-2.472V2.472C1 1.104 2.104 0 3.46 0h16.08zm-4.632 15.672c2.652-.084 3.672-1.824 3.672-1.824 0-3.864-1.728-6.996-1.728-6.996-1.728-1.296-3.372-1.26-3.372-1.26l-.168.192c2.04.624 2.988 1.524 2.988 1.524a9.787 9.787 0 0 0-3.612-1.152 10.13 10.13 0 0 0-2.424.024c-.072 0-.132.012-.204.024-.42.036-1.44.192-2.724.756-.444.204-.708.348-.708.348s.996-.948 3.156-1.572l-.12-.144s-1.644-.036-3.372 1.26c0 0-1.728 3.132-1.728 6.996 0 0 1.008 1.74 3.66 1.824 0 0 .444-.54.804-.996-1.524-.456-2.1-1.416-2.1-1.416l.336.204.048.036.047.027.014.006.047.027c.3.168.6.3.876.408.492.192 1.08.384 1.764.516.9.168 1.956.228 3.108.012.564-.096 1.14-.264 1.74-.516.42-.156.888-.384 1.38-.708 0 0-.6.984-2.172 1.428.36.456.792.972.792.972zM8.52 11.94c0 .684.504 1.236 1.116 1.236.624 0 1.116-.552 1.116-1.236.012-.684-.492-1.236-1.116-1.236-.612 0-1.116.552-1.116 1.236zm3.996 0c0 .684.504 1.236 1.116 1.236.624 0 1.116-.552 1.116-1.236 0-.684-.492-1.236-1.116-1.236-.612 0-1.116.552-1.116 1.236z" />
              </svg>
            )}
          </button>
        )}
        {discordOn && isToc && realWinners.length > 0 && (
          <button
            class={`nav-btn discord-btn discord-${postState.status}`}
            onClick={postAll}
            disabled={postState.status !== 'idle'}
            title={`Post all ${realWinners.length} awards to Discord`}
          >
            {postState.status === 'busy' && postState.progress ? (
              <span class="discord-progress">
                {postState.progress.phase === 'done'
                  ? '✓'
                  : `${(postState.progress.i ?? 0) + 1}/${postState.progress.total}`}
              </span>
            ) : (
              <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
                <path d="M19.54 0c1.356 0 2.46 1.104 2.46 2.472v21.528l-2.58-2.28-1.452-1.344-1.536-1.428.636 2.22H3.46c-1.356 0-2.46-1.104-2.46-2.472V2.472C1 1.104 2.104 0 3.46 0h16.08zm-4.632 15.672c2.652-.084 3.672-1.824 3.672-1.824 0-3.864-1.728-6.996-1.728-6.996-1.728-1.296-3.372-1.26-3.372-1.26l-.168.192c2.04.624 2.988 1.524 2.988 1.524a9.787 9.787 0 0 0-3.612-1.152 10.13 10.13 0 0 0-2.424.024c-.072 0-.132.012-.204.024-.42.036-1.44.192-2.724.756-.444.204-.708.348-.708.348s.996-.948 3.156-1.572l-.12-.144s-1.644-.036-3.372 1.26c0 0-1.728 3.132-1.728 6.996 0 0 1.008 1.74 3.66 1.824 0 0 .444-.54.804-.996-1.524-.456-2.1-1.416-2.1-1.416l.336.204.048.036.047.027.014.006.047.027c.3.168.6.3.876.408.492.192 1.08.384 1.764.516.9.168 1.956.228 3.108.012.564-.096 1.14-.264 1.74-.516.42-.156.888-.384 1.38-.708 0 0-.6.984-2.172 1.428.36.456.792.972.792.972zM8.52 11.94c0 .684.504 1.236 1.116 1.236.624 0 1.116-.552 1.116-1.236.012-.684-.492-1.236-1.116-1.236-.612 0-1.116.552-1.116 1.236zm3.996 0c0 .684.504 1.236 1.116 1.236.624 0 1.116-.552 1.116-1.236 0-.684-.492-1.236-1.116-1.236-.612 0-1.116.552-1.116 1.236z" />
              </svg>
            )}
          </button>
        )}
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
