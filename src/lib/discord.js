import { toPng } from 'html-to-image'

const WEBHOOK_URL = import.meta.env.VITE_DISCORD_WEBHOOK_URL || ''

export const isDiscordEnabled = () => import.meta.env.DEV && !!WEBHOOK_URL

const STAT_LABELS = {
  speed: 'Speed',
  stamina: 'Stamina',
  power: 'Power',
  guts: 'Guts',
  wit: 'Wit',
}

const ACCENT_COLOR = 0xff8a3c

// Mirrors the per-event accent overrides in themes/uma/styles.css so the embed
// stripe matches the slide image it's posted alongside.
const EVENT_ACCENT = {
  CM16: 0x5cb85c,
  CM17: 0xef5350,
  CM18: 0x9b59b6,
}

function buildEmbed(slide, event) {
  const stats = slide.stats || {}
  const statsLine = Object.keys(STAT_LABELS)
    .filter((k) => stats[k] != null)
    .map((k) => `**${STAT_LABELS[k]}** ${stats[k].toLocaleString()}`)
    .join(' • ')

  const fields = []
  if (slide.time) fields.push({ name: 'Finals Time', value: `\`${slide.time}\``, inline: true })
  if (slide.result) fields.push({ name: 'Result', value: slide.result, inline: true })
  if (event.track) fields.push({ name: 'Track', value: event.track, inline: true })
  if (statsLine) fields.push({ name: 'Stats', value: statsLine, inline: false })

  return {
    title: slide.trainee_name,
    description: slide.quote ? `> *${slide.quote}*` : undefined,
    color: EVENT_ACCENT[event?.id] ?? ACCENT_COLOR,
    author: { name: `${slide.ign} — Oshi's Champion Awardee` },
    footer: { text: `${event.name} • Moomoocows` },
    fields,
    image: { url: 'attachment://slide.png' },
  }
}

export async function captureSlide(stageEl) {
  if (!stageEl) throw new Error('No slide element to capture')
  const dataUrl = await toPng(stageEl, {
    pixelRatio: 2,
    cacheBust: true,
    backgroundColor: '#0b0d12',
  })
  const res = await fetch(dataUrl)
  return await res.blob()
}

async function postOne(slide, event, screenshotBlob, { sleepBefore = 0 } = {}) {
  if (!WEBHOOK_URL) throw new Error('VITE_DISCORD_WEBHOOK_URL not set')
  if (sleepBefore) await new Promise((r) => setTimeout(r, sleepBefore))

  const threadName = `${event.name} — ${slide.ign}`.slice(0, 100)
  const payload = {
    thread_name: threadName,
    embeds: [buildEmbed(slide, event)],
    allowed_mentions: { parse: [] },
  }

  const form = new FormData()
  form.append('payload_json', JSON.stringify(payload))
  form.append('files[0]', screenshotBlob, 'slide.png')

  const res = await fetch(`${WEBHOOK_URL}?wait=true`, { method: 'POST', body: form })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Discord ${res.status}: ${text}`)
  }
  return res.json()
}

export async function postSlide({ slide, event, stageEl }) {
  const blob = await captureSlide(stageEl)
  return postOne(slide, event, blob)
}

export async function postAllSlides({ slides, event, captureFor, onProgress }) {
  const results = []
  for (let i = 0; i < slides.length; i++) {
    const slide = slides[i]
    onProgress?.({ phase: 'capturing', i, total: slides.length, slide })
    const blob = await captureFor(slide, i)
    onProgress?.({ phase: 'posting', i, total: slides.length, slide })
    try {
      const r = await postOne(slide, event, blob, { sleepBefore: i === 0 ? 0 : 1200 })
      results.push({ slide, ok: true, response: r })
    } catch (e) {
      results.push({ slide, ok: false, error: String(e) })
    }
  }
  onProgress?.({ phase: 'done', total: slides.length })
  return results
}
