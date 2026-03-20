# Uma Slides

Browser-based slideshow for Umamusume Virgo Cup "Oshi's Champion Awardee" presentations. Replaces the previous Canva workflow with an automated data pipeline and interactive viewer.

## Quick Start

```bash
npm install
pip install pandas pyarrow   # for the preprocessor

# Generate slide data (run per event)
python3 scripts/preprocess.py --repo ../Umamusume_Virgo_Cup_Dashboard --event CM9
python3 scripts/preprocess.py --repo ../Umamusume_Virgo_Cup_Dashboard --event CM10

# Start dev server
npm run dev
```

Open `http://localhost:5173` — pick an event from the index, then navigate slides.

## Project Structure

```
uma-slides/
├── scripts/
│   └── preprocess.py          # Data pipeline: CSV/Parquet → JSON + images
├── src/
│   ├── app.jsx                # Root: event picker ↔ slide viewer routing
│   ├── components/
│   │   ├── EventPicker.jsx    # Landing page with event cards
│   │   ├── SlideViewer.jsx    # Navigation, transitions, fullscreen
│   │   ├── OshiAwardSlide.jsx # Individual slide layout
│   │   └── StatsBar.jsx       # Speed/Stamina/Power/Guts/Wit display
│   ├── data/
│   │   ├── index.json         # Generated manifest of all events
│   │   ├── slides-cm9.json    # Generated slide data per event
│   │   └── slides-cm10.json
│   └── styles/
│       └── slides.css         # All slide and viewer styling
├── public/
│   ├── umas/                  # Character images (cropped + full art)
│   ├── aquarius_icon.png      # CM event icons
│   ├── capricorn_icon.png
│   └── moologo2.png           # Moomoocows logo
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

### Adding a new event

Add an entry to `EVENT_CONFIG` in `preprocess.py` with the event's name, icon, track info, and file paths, then run the script.

### Full art images

Place full-body race art in `public/umas/` using the naming convention `CharName_(Race).png` (e.g. `Gold_Ship_(Race).png`). The preprocessor auto-detects these and assigns them to matching slides.

When multiple costumes share a base character (e.g. two Rice Shower variants), the `DEFAULT_COSTUME` dict in `preprocess.py` controls which costume gets the base `(Race)` art. Non-default costumes fall back to their cropped headshot.

## Viewer Features

- **Event picker** — landing page to select a Champion's Meeting
- **Animated transitions** — crossfade with directional shift between slides, character art slides in with staggered ghost effect
- **Keyboard shortcuts** — Arrow keys to navigate, `F` to toggle fullscreen, `Esc` to exit
- **Click zones** — left/right 10% of the slide area for prev/next navigation
- **Fullscreen mode** — button in top-right corner for recording/presentation
- **Responsive 16:9 layout** — scales to fill the viewport while maintaining aspect ratio

## Tech Stack

- **Preact** + **Vite** — lightweight frontend
- **Python** + **pandas/pyarrow** — data preprocessing
- **CSS** — custom styling with Montserrat font, gradient text, blurred character backgrounds, animated transitions
