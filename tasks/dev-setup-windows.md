# Dev Environment Setup — Windows

A one-time setup guide for working on `uma-slides` from a Windows machine. Aim is ~15 minutes from zero to a running dev server.

> **TL;DR:** Install Git → Node LTS → (optional) `uv` for Python → clone → `npm install` → `npm run dev`. For asset-only tasks (e.g. [UMA-13](./UMA-13-cm13-assets.md)), you can skip Python entirely.

---

## 1. Prerequisites

Install in order. All three are free.

### 1a. Git for Windows
- Download: https://git-scm.com/download/win
- During install, accept defaults **except**:
  - "Adjusting your PATH environment" → **Git from the command line and also from 3rd-party software**
  - "Configuring the line ending conversions" → **Checkout as-is, commit Unix-style line endings** (prevents diffs polluting with `^M`)
- Verify: open **PowerShell** and run `git --version` → should print `git version 2.x.x`

### 1b. Node.js (LTS)
- Download: https://nodejs.org/en/download (pick the **LTS** Windows installer)
- Accept defaults
- Verify in PowerShell: `node --version` (should be ≥ 20) and `npm --version`

### 1c. (Only if running the data pipeline) uv — Python package manager
You only need this if you'll run `scripts/preprocess.py`. For pure asset/UI work, skip this.

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Close and reopen PowerShell after install. Verify: `uv --version`.

---

## 2. Recommended editor

[VS Code](https://code.visualstudio.com/) — free. Suggested extensions:
- **ESLint**
- **Prettier — Code formatter**

Open the project folder via *File → Open Folder*. The integrated terminal (View → Terminal) defaults to PowerShell, which is fine for everything below.

---

## 3. Clone and install

In PowerShell, pick a working directory (e.g. `C:\Users\<you>\Dev\`) and:

```powershell
cd C:\Users\<you>\Dev
git clone https://github.com/TheCing/uma-slides.git
cd uma-slides

# Install JS deps (Vite, Preact, etc.)
npm install
```

If `npm install` complains about Python or Visual Studio Build Tools — ignore it. Our deps are pure JS and the warnings are spurious noise from optional native modules.

---

## 4. Run the dev server

```powershell
npm run dev
```

Open the URL it prints (default: `http://localhost:5173/uma-slides/`). You should see the event-picker landing page with CM9–CM13 tiles. Click any to view that event's slides.

Stop the server with **Ctrl+C** in the terminal.

---

## 5. (Optional) Run the data pipeline

Skip unless your task involves regenerating slide JSON.

```powershell
# One-time install of Python deps
uv sync

# Generate a single event (example: CM13)
uv run python scripts/preprocess.py --event CM13 --repo C:\path\to\UmaOCRData
```

The `--repo` flag points at a clone of [UmaOCRData](https://github.com/ZuseGD/UmaOCRData) — ask the project lead for the current data source path.

---

## 6. Windows-specific gotchas

| Issue | Fix |
|---|---|
| **Filenames with `[`, `]`, `(`, `)` look mangled in PowerShell tab-completion** | Wrap the filename in single quotes: `'[Costume Name] Character.png'`. The brackets are literal characters in our filenames, not glob wildcards. |
| **Long paths error during clone or install** | Run `git config --system core.longpaths true` (admin PowerShell) before cloning. |
| **`npm run dev` fails with EACCES or port-in-use** | Vite picks a free port automatically — re-read the terminal output for the actual URL. If something else is squatting `5173`, just trust whatever Vite prints. |
| **Line-ending mismatches in PRs** | If you ever see every line marked as changed in a diff, your editor saved the file with CRLF. Configure your editor to save with LF, or run `git config core.autocrlf input` in the repo. |
| **`uv` says command not found** | Close and reopen PowerShell after installing uv — it has to pick up the new PATH. |
| **Image filenames lose unicode characters** when pasted from web sources (e.g. Japanese punctuation in costume names) | Save the file via *right-click → Save image as…*, then **rename it manually** by copy-pasting the exact filename from the ticket. Don't trust browser auto-naming. |

---

## 7. First-task workflow

```powershell
# Make a feature branch
git checkout -b my-task-name

# ... do your work ...

git add .
git commit -m "Short description of what you did"
git push -u origin my-task-name
```

Then go to https://github.com/TheCing/uma-slides → the repo will prompt you to open a PR. Title it descriptively, ping the project lead for review.

---

## 8. Sanity checklist before opening a PR

- [ ] `npm run dev` starts cleanly with no console errors
- [ ] Click through every event affected by your change; no broken images, no JS errors in DevTools (F12)
- [ ] If you added images: filenames match exactly (case, spacing, brackets), all `.png`
- [ ] You haven't committed `node_modules/`, `dist/`, or `.env` files (the `.gitignore` handles this, but double-check `git status` before committing)
- [ ] Branch is rebased on (or up to date with) `main`

---

## 9. Getting help

If you're stuck more than 15 minutes on setup, ping the project lead with:
- The exact command you ran
- The full terminal output (paste as a code block, don't screenshot)
- Output of `node --version`, `npm --version`, `git --version`
