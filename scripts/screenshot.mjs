// Capture a screenshot of a dev-server page for visual/CSS verification.
//
// Usage:
//   node scripts/screenshot.mjs <url> <outPath> [width] [height]
//
// Examples:
//   node scripts/screenshot.mjs "http://localhost:5174/uma-slides/#/CM14" tmp/cm14-toc.png
//   node scripts/screenshot.mjs "http://localhost:5174/uma-slides/#/CM14/cing" tmp/slide.png 1280 720
import { chromium } from 'playwright'

const [url, outPath, w, h] = process.argv.slice(2)
if (!url || !outPath) {
  console.error('Usage: node scripts/screenshot.mjs <url> <outPath> [width] [height]')
  process.exit(1)
}
const width = Number(w) || 1280
const height = Number(h) || 720

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 2 })

const errors = []
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()) })
page.on('pageerror', (e) => errors.push(String(e)))

await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 })
// Let fonts/images and any entrance transitions settle.
await page.waitForTimeout(1200)
await page.screenshot({ path: outPath })
await browser.close()

console.log(`saved ${outPath} (${width}x${height})`)
if (errors.length) {
  console.log(`\nconsole errors (${errors.length}):`)
  for (const e of errors.slice(0, 20)) console.log('  - ' + e)
}
