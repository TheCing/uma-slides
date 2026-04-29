// Hash-router primitives. Format: "#/<eventId>" or "#/<eventId>/<ignSlug>"
// We use the hash so the app works on any static host without redirects.

export function parseHash(hash) {
  const raw = (hash || '').replace(/^#\/?/, '')
  if (!raw) return { eventId: null, ignSlug: null }
  const parts = raw.split('/').filter(Boolean).map(decodeURIComponent)
  return {
    eventId: parts[0] ? parts[0].toUpperCase() : null,
    ignSlug: parts[1] ? parts[1].toLowerCase() : null,
  }
}

export function buildHash(eventId, ign) {
  if (!eventId) return '#/'
  const e = encodeURIComponent(eventId)
  if (!ign) return `#/${e}`
  return `#/${e}/${encodeURIComponent(ign.toLowerCase())}`
}

export function findSlideIndex(slides, ignSlug) {
  if (!ignSlug) return 0
  const i = slides.findIndex(s => s.ign.toLowerCase() === ignSlug)
  return i >= 0 ? i : 0
}
