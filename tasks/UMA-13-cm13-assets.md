# [UMA-13] Add missing CM13 character art assets

---

## Description

The CM13 (2nd Taurus Cup) event slides are live but several winner umas are missing their character images. We need to source 5 character headshots, 1 event icon, and verify some optional full-art images. No code changes required — pure asset drop + commit.

---

## 1. Repo setup

```bash
# Clone the repo
git clone https://github.com/TheCing/uma-slides.git
cd uma-slides

# Install JS deps
npm install

# (Optional, only if you want to run the slideshow locally to verify)
npm run dev
# Open http://localhost:5173/uma-slides/ → pick "2nd Taurus Cup"
```

You don't need Python / `uv sync` for this task — you're only adding image files.

---

## 2. Where to source the images

Each missing image is a **Umamusume "outfit" sprite**. Canonical sources:

- **Headshots / cropped art** → [Gametora character pages](https://gametora.com/umamusume/characters) — find the character, then locate the listed costume variant. Right-click → save the cropped portrait.
- **Full-art / race art (`*_(Race).png`)** → [Umamusume Pretty Derby Wiki](https://umamusume.fandom.com/) — character page → "Race Outfit" or the costume's individual page. Use the transparent-background race art if available.
- https://wiki.biligame.com/umamusume/繁中赛马娘图鉴

If a costume doesn't have a transparent crop on Gametora, grab the wiki's race art and we'll use that as the full-art fallback.

---

## 3. Where to put the images

All character images go into `public/umas/`. Filename convention is **strict** — must match exactly:

- **Headshot:** `[Costume Name] Character Name.png` (with literal square brackets, exact spacing)
- **Race art (full-art):** `Character_Name_(Race).png` (underscores, parens around `Race`)
- **Event icon:** `public/taurus_icon.png` (lowercase, in `public/`, not `public/umas/`)

Important:
- Use `.png` only (not `.webp` / `.jpg`)
- Do **not** URL-encode special characters (e.g. save as `(`, not `%28`)

---

## 4. Asset checklist

### Required (slides currently broken without these):

- [ ] `public/umas/[Line Breakthrough] Mejiro Palmer.png`
- [ ] `public/umas/[Beyond the Horizon] Tokai Teio.png`
- [ ] `public/umas/[Precise Chocolatier] Eishin Flash.png`
- [ ] `public/umas/[Brunissage Line] Mejiro Bright.png`
- [ ] `public/taurus_icon.png` — event tile icon (use a Taurus zodiac glyph or pull from same source as the existing `public/aries_icon.png` / `public/pisces_icon.png` so it visually matches)

### Optional (slides render via existing full-art, but headshots improve fallback):

- [ ] `public/umas/[pf. Winning Equation...] Biwa Hayahide.png`
- [ ] `public/umas/[Shooting Star Revue] Fuji Kiseki.png`

### Bonus — try to find race art for the 4 required umas above:

- [ ] `public/umas/Mejiro_Palmer_(Race).png`
- [ ] `public/umas/Tokai_Teio_(Race).png`
- [ ] `public/umas/Eishin_Flash_(Race).png`
- [ ] `public/umas/Mejiro_Bright_(Race).png`

(If race art isn't easily available for one or more, that's fine — the headshot alone is enough.)

---

## 5. Acceptance criteria

1. All "Required" files exist in the listed paths with **exact** filenames (case + spacing + brackets).
2. Files are `.png`, not `.webp` / `.jpg`.
3. Run `npm run dev`, open the **2nd Taurus Cup** event, and confirm every slide shows a character image (no broken-image icons, no blank silhouettes).
4. The CM13 tile on the event-picker landing page shows a Taurus icon (not the default placeholder).

---

## 6. Submit

```bash
git checkout -b cm13-assets
git add public/umas/ public/taurus_icon.png
git commit -m "Add CM13 character art and Taurus event icon"
git push -u origin cm13-assets
```

Open a PR against `main` titled **"CM13 character assets"** and tag me for review. Include before/after screenshots of the CM13 slide deck (one screenshot per slide is fine).