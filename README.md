# Uma Slides

Browser-based slideshow for Umamusume Virgo Cup "Oshi's Champion Awardee" presentations. Replaces the previous Canva workflow with an automated data pipeline and interactive viewer.

## Quick Start

```bash
npm install
uv sync                      # install Python deps (pandas, pyarrow)

# Generate slide data (run per event)
uv run python scripts/preprocess.py --repo ../Umamusume_Virgo_Cup_Dashboard --event CM9
uv run python scripts/preprocess.py --repo ../Umamusume_Virgo_Cup_Dashboard --event CM10

# Start dev server
npm run dev
```

Open `http://localhost:5173/uma-slides/` — pick an event from the index, then navigate slides.

## Project Structure

```
uma-slides/
├── scripts/
│   └── preprocess.py          # Data pipeline: CSV/Parquet → JSON + images
├── src/
│   ├── app.jsx                # Root: event picker ↔ slide viewer routing
│   ├── components/
│   │   ├── EventPicker.jsx    # Landing page with event cards
│   │   └── SlideViewer.jsx    # Navigation, transitions, fullscreen
│   ├── themes/
│   │   ├── registry.js        # Theme name → component mapping
│   │   ├── default/           # "default" dark theme
│   │   │   ├── OshiAwardSlide.jsx
│   │   │   ├── StatsBar.jsx
│   │   │   └── styles.css
│   │   └── uma/               # "uma" theme (in-game design language)
│   │       ├── UmaSlide.jsx
│   │       ├── UmaStatsBar.jsx
│   │       ├── styles.css
│   │       └── horseshoe.svg  # Tiled background icon
│   ├── utils/
│   │   └── names.js           # Display name helpers (costume prefix stripping)
│   ├── data/
│   │   ├── index.json         # Generated manifest of all events
│   │   ├── slides-cm9.json    # Generated slide data per event
│   │   └── slides-cm10.json
│   └── styles/
│       └── slides.css         # Shared viewer/controls/transition styles
├── public/
│   ├── umas/                  # Character images (cropped + full art)
│   ├── aquarius_icon.png      # CM event icons
│   ├── capricorn_icon.png
│   ├── horseshoe.svg          # Horseshoe icon source
│   └── moologo2.png           # Moomoocows logo
├── pyproject.toml             # Python deps (uv)
└── package.json
```

## Data Pipeline

`scripts/preprocess.py` reads from a local clone of [ZuseGD/Umamusume_Virgo_Cup_Dashboard](https://github.com/ZuseGD/Umamusume_Virgo_Cup_Dashboard):

1. Loads finals CSV, podium parquet, and statsheet parquet for the given event
2. Finds players who declared oshi and placed 1st
3. Filters to winners whose uma was the **only** one of its kind to win a race (the "unique oshi" criteria)
4. Extracts stats (Speed, Stamina, Power, Guts, Wit) and optional quote
5. Outputs `src/data/slides-{event}.json` and updates `src/data/index.json`
6. Copies uma character images to `public/umas/`

When the podium OCR has a truncated or mismatched IGN, the script falls back to the stats table to resolve the player's trainee name, then cross-references back to the podium. A `claimed_umas` set prevents the same uma from being assigned to multiple players.

### Adding a new event

Add an entry to `EVENT_CONFIG` in `preprocess.py` with the event's name, icon, theme, track info, and file paths, then run the script. The `theme` field selects which visual theme to use (defaults to `"default"`).

### Adding a new theme

1. Create a folder under `src/themes/` (e.g. `src/themes/neon/`)
2. Add a slide component (`NeonSlide.jsx`) and its own `styles.css`
3. The component receives `{ slide, event, allTraineeNames }` props — the data contract is the same across all themes
4. Register it in `src/themes/registry.js`
5. Set `"theme": "neon"` in the event's `EVENT_CONFIG` entry

### Full art images

Place full-body race art in `public/umas/` using the naming convention `CharName_(Race).png` (e.g. `Gold_Ship_(Race).png`). The preprocessor auto-detects these and assigns them to matching slides.

When multiple costumes share a base character (e.g. two Rice Shower variants), the `DEFAULT_COSTUME` dict in `preprocess.py` controls which costume gets the base `(Race)` art. Non-default costumes can have explicit art via the `ALT_ART` dict (e.g. `Rice_Shower_(Alt).png` for Vampire Makeover).

### Display names

The subtitle strips the costume bracket prefix by default (e.g. `[Red Strife] Gold Ship` → `Gold Ship`). When multiple costumes of the same character appear in one event's slides, the prefix is kept for disambiguation and displayed after the base name (e.g. `Gold City [Autumn Cosmos]`). This logic lives in `src/utils/names.js`.

## Themes

### Default (dark)

Dark gradient background with animated ambient drift. White gradient IGN text, character art with ghost effect, animated slide-in. Stats displayed as large numbers with labels. Used by CM9.

### Uma (in-game design language)

Warm cream palette inspired by the Uma Musume in-game UI. Features Nunito + Quicksand fonts, orange gradient IGN text, ribbon-style title, glassmorphism quote panel, color-coded stat bars with letter grades (G through S+), floating glow orbs, sparkle decorations, shimmer effect on character art, and a tiled horseshoe background pattern. Used by CM10.

## Viewer Features

- **Event picker** — landing page to select a Champion's Meeting
- **Animated transitions** — crossfade with directional shift between slides, character art slides in with staggered ghost effect
- **Keyboard shortcuts** — Arrow keys to navigate, `F` to toggle fullscreen, `Esc` to exit
- **Click zones** — left/right 10% of the slide area for prev/next navigation
- **Fullscreen mode** — button in top-right corner for recording/presentation
- **Responsive 16:9 layout** — scales to fill the viewport while maintaining aspect ratio
- **Theme system** — each event can use a different slide theme; themes are self-contained component + CSS folders
- **Dynamic IGN sizing** — font scales down for long names, stays large for short ones

## Deployment

Deployed to GitHub Pages via GitHub Actions on push to `main`. The Vite `base` is set to `/uma-slides/` for correct asset resolution.

## Tech Stack

- **Preact** + **Vite** — lightweight frontend
- **Python** + **pandas/pyarrow** (managed by **uv**) — data preprocessing
- **CSS** — custom styling, gradient text, animated backgrounds, transitions
