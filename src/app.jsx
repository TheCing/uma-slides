import { useState, useEffect, useCallback } from 'preact/hooks'
import { SlideViewer } from './components/SlideViewer'
import { EventPicker } from './components/EventPicker'
import { parseHash, buildHash } from './utils/route'
import index from './data/index.json'
import './styles/slides.css'

const dataModules = import.meta.glob('./data/slides-*.json', { eager: true })

function getEventByIdOrFile(idOrFile) {
  if (!idOrFile) return null
  const ev = index.events.find(
    e => e.id === idOrFile || e.file === idOrFile,
  )
  return ev || null
}

function getEventData(file) {
  const match = Object.entries(dataModules).find(([path]) => path.endsWith(file))
  return match ? match[1].default : null
}

export function App() {
  const [route, setRoute] = useState(() => parseHash(window.location.hash))

  useEffect(() => {
    const onChange = () => setRoute(parseHash(window.location.hash))
    window.addEventListener('hashchange', onChange)
    return () => window.removeEventListener('hashchange', onChange)
  }, [])

  const selectEvent = useCallback((fileOrId) => {
    const ev = getEventByIdOrFile(fileOrId)
    window.location.hash = buildHash(ev?.id || fileOrId)
  }, [])

  const goHome = useCallback(() => {
    window.location.hash = '#/'
  }, [])

  const updateSlideHash = useCallback((eventId, ign) => {
    const target = buildHash(eventId, ign)
    if (window.location.hash !== target) {
      // Use replaceState so per-slide navigation doesn't clutter back-history
      history.replaceState(null, '', target)
    }
  }, [])

  const event = getEventByIdOrFile(route.eventId)

  if (!event) {
    return <EventPicker events={index.events} onSelect={selectEvent} />
  }

  const data = getEventData(event.file)
  if (!data) return null

  return (
    <SlideViewer
      slides={data.slides}
      event={data.event}
      eventId={event.id}
      initialIgnSlug={route.ignSlug}
      onBack={goHome}
      onSlideChange={updateSlideHash}
    />
  )
}
