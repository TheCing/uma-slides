#!/usr/bin/env python3
"""
Preprocess Umamusume dashboard data into slide JSON for the Preact viewer.

Usage:
    python3 scripts/preprocess.py --repo ../Umamusume_Virgo_Cup_Dashboard --event CM10
    python3 scripts/preprocess.py --event CM11   # uses local data in src/data/
"""

import argparse
import json
import os
import re
import shutil
import unicodedata
import urllib.parse
import pandas as pd
from pathlib import Path

EVENT_CONFIG = {
    "CM9": {
        "name": "Capricorn Cup",
        "icon": "capricorn_icon.png",
        "theme": "default",
        "distance": "Sprint",
        "surface": "Turf",
        "track": "Chukyo 1200m",
        "finals_csv": "data/cm9_finals.csv",
        "statsheet": "data/cm9_finals_statsheet_1.parquet",
        "podium": "data/cm9_finals_podium_1.parquet",
    },
    "CM10": {
        "name": "Aquarius Cup",
        "icon": "aquarius_icon.png",
        "theme": "uma",
        "distance": "Mile",
        "surface": "Dirt",
        "track": "Tokyo Dirt 1600m",
        "finals_csv": "data/cm10_finals.csv",
        "statsheet": "data/cm10_finals_statsheet_0.parquet",
        "podium": "data/cm10_finals_podium_0.parquet",
    },
    "CM11": {
        "name": "Pisces Cup",
        "icon": "pisces_icon.png",
        "theme": "uma",
        "distance": "Long",
        "surface": "Turf",
        "track": "Hanshin Turf 3200m",
        "finals_csv": "sheet_cache_merged_1.csv",
        "statsheet": "cm11_finals_statsheet_0.parquet",
        "podium": "cm11_finals_podium_0.parquet",
        "local": True,
    },
    "CM12": {
        "name": "Aries Cup",
        "icon": "aries_icon.png",
        "theme": "uma",
        "distance": "Medium",
        "surface": "Turf",
        "track": "Nakayama Turf 2000m",
        "finals_csv": "data/cm12_finals.csv",
        "statsheet": "data/cm12_finals_statsheet_0.parquet",
        "podium": "data/cm12_finals_podium_0.parquet",
    },
}

COL_IGN = "Unique display name"
COL_OSHI = 'Did you build an "oshi"/niche uma ace this CM?'
COL_QUOTE = 'Optional - Quote in case you win an "Oshi award" this CM to be used in the award'
COL_RESULT = "Finals result?"
COL_LEAGUE = "League Selection"
COL_FINALS_GROUP = "A or B Finals?"
COL_WINNER_NAME = "Finals - Winner - Name"
COL_WINNER_TIME = "Finals - Winner - Time (optional)"
COL_PODIUM_UPLOAD = "Finals - Results List - Upload Screenshot"
COL_STAT_UPLOAD_1 = "Optional - Finals - Winner - Screenshot - Stat Screen (First Image)"
COL_STAT_UPLOAD_2 = "Optional - Finals - Winner - Screenshot - Stat Screen (Second Image)"
LEAGUE_GRADED_PREFIX = "Graded"

DEFAULT_COSTUME = {
    "Rice Shower": "[Rosy Dreams] Rice Shower",
}

ALT_ART = {
    "[Vampire Makeover!] Rice Shower": "Rice_Shower_(Alt).png",
}

# Maps survey IGN -> trainer_name as it appears in the podium/stats parquet.
# Use when the player submitted their data under a different name and fuzzy
# matching would fail (case-insensitive lookup).
IGN_ALIASES = {
    "mahoneyos": "Mitchell",  # CM11 — documented IGN inconsistency
}


def resolve_alias(ign):
    """Return the aliased trainer name for an IGN, or None."""
    return IGN_ALIASES.get(str(ign).lower())


def load_overrides(event_id, project_root):
    """Load manual override directives for an event.

    File format: overrides/{event}.json. Two supported shapes:
      1. Bare list — treated as overrides (back-compat).
      2. Dict with optional keys:
         - "overrides": list of slide entries to inject {ign, trainee_name, ...}
         - "patches":   list of field patches {ign, ...fields...} applied to
                        any matching slide (auto or overridden) by IGN.

    Override entries: at minimum {ign, trainee_name}. Optional time/quote
    fall back to the player's CSV row if omitted. Stats come from the
    statsheet by ign+trainee_name (or zeroes if missing).

    Patch entries: any of {time, quote, stats, trainee_name, uma_image} —
    these overwrite the corresponding fields on the slide whose ign matches.
    """
    path = project_root / "overrides" / f"{event_id.lower()}.json"
    if not path.exists():
        return [], []
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, list):
        return data, []
    return data.get("overrides", []), data.get("patches", [])


def main():
    parser = argparse.ArgumentParser(description="Generate oshi award slide data")
    parser.add_argument("--repo", help="Path to Umamusume_Virgo_Cup_Dashboard repo (optional for local events)")
    parser.add_argument("--event", required=True, choices=EVENT_CONFIG.keys(), help="Event ID")
    args = parser.parse_args()

    cfg = EVENT_CONFIG[args.event]
    project_root = Path(__file__).resolve().parent.parent

    if cfg.get("local"):
        data_base = project_root / "src" / "data"
        umas_dir = None
    else:
        if not args.repo:
            parser.error(f"--repo is required for {args.event}")
        data_base = Path(args.repo).resolve()
        umas_dir = data_base / "assets" / "umas"

    finals_df = pd.read_csv(data_base / cfg["finals_csv"])
    podium_df = pd.read_parquet(data_base / cfg["podium"])
    stats_df = pd.read_parquet(data_base / cfg["statsheet"])

    print(f"Loaded {len(finals_df)} CSV rows, {len(podium_df)} podium rows, {len(stats_df)} stat rows")

    # --- Candidate pool: strict CSV-side filter (Step 1) ---
    # League=Graded, Result=1st, SubmitPodium present, SubmitStat present.
    # Then count declared-winner names; uniques are umas declared by exactly
    # one qualified 1st-place player (uniqueness is CSV-side, not podium-side).
    pool_filter = (
        (finals_df[COL_RESULT] == "1st")
        & finals_df[COL_LEAGUE].astype(str).str.startswith(LEAGUE_GRADED_PREFIX)
        & finals_df[COL_PODIUM_UPLOAD].notna()
    )
    if COL_FINALS_GROUP in finals_df.columns:
        pool_filter &= (finals_df[COL_FINALS_GROUP] == "A Finals")
    if COL_STAT_UPLOAD_2 in finals_df.columns:
        pool_filter &= (
            finals_df[COL_STAT_UPLOAD_1].notna() | finals_df[COL_STAT_UPLOAD_2].notna()
        )
    else:
        pool_filter &= finals_df[COL_STAT_UPLOAD_1].notna()
    candidate_pool = finals_df[pool_filter & finals_df[COL_WINNER_NAME].notna()].copy()
    print(f"Strict candidate pool (Graded/1st/SubmitPodium/SubmitStat): {len(candidate_pool)}")

    declared_counts = candidate_pool[COL_WINNER_NAME].value_counts()
    unique_winner_names = set(declared_counts[declared_counts == 1].index)
    print(f"Unique declared winners (count==1 in pool): {len(unique_winner_names)}")

    # --- Step 2: apply oshi=Yes last so non-oshi unique winners drop out ---
    oshi_unique = candidate_pool[
        (candidate_pool[COL_OSHI] == "Yes")
        & candidate_pool[COL_WINNER_NAME].isin(unique_winner_names)
    ]
    print(f"Oshi-claiming unique winners: {len(oshi_unique)}")

    # Podium reference (for time lookup + diagnostics; no longer drives uniqueness)
    race_winners = podium_df[podium_df["placement"] == 1]

    slides = []
    images_needed = set()
    claimed_umas = set()

    for _, row in oshi_unique.iterrows():
        ign = row[COL_IGN]
        csv_trainee = row[COL_WINNER_NAME]
        quote = row[COL_QUOTE] if pd.notna(row[COL_QUOTE]) else ""
        csv_time = row[COL_WINNER_TIME] if COL_WINNER_TIME in row and pd.notna(row[COL_WINNER_TIME]) else ""
        alias = resolve_alias(ign)
        ign_candidates = [ign] + ([alias] if alias else [])

        # Resolve canonical trainee name from podium (preferred) or stats parquet.
        # CSV-declared names are often informal (e.g. "Mayano Top Gun (Wedding)")
        # while parquets carry the canonical bracket-tag form used for image filenames.
        ign_lower = ign.lower()
        alias_lower = alias.lower() if alias else None

        def _trainer_fuzzy_match(t):
            t = str(t).lower()
            return (t == ign_lower
                    or (alias_lower and t == alias_lower)
                    or t.startswith(ign_lower[:3])
                    or ign_lower.startswith(t[:3])
                    or t in ign_lower
                    or ign_lower in t)

        # Normalize for cross-source comparison: drop bracket-tags and parenthetical
        # suffixes so "Mayano Top Gun (Wedding)" ≈ "[Sunlight Bouquet] Mayano Top Gun".
        def _base_name(n):
            if not n or pd.isna(n):
                return ""
            s = re.sub(r"\[.*?\]\s*", "", str(n))
            s = re.sub(r"\s*\([^)]+\)\s*$", "", s)
            return s.strip().lower()

        csv_base = _base_name(csv_trainee)

        pod_match = race_winners[race_winners["trainer_name"].isin(ign_candidates)]
        if pod_match.empty:
            uma_rows = race_winners[race_winners["trainee_name"] == csv_trainee]
            for _, cw in uma_rows.iterrows():
                if _trainer_fuzzy_match(cw["trainer_name"]):
                    pod_match = uma_rows[uma_rows.index == cw.name]
                    print(f"  Resolved {ign} podium via fuzzy match (trainer={cw['trainer_name']})")
                    break

        # Reject podium match if its uma disagrees with CSV declaration — this
        # catches cases where the player's only podium row is an opponent's win
        # in a race they lost (data inconsistency).
        if not pod_match.empty:
            pod_trainee = pod_match.iloc[0]["trainee_name"]
            if csv_base and _base_name(pod_trainee) != csv_base:
                print(f"  REJECT podium for {ign}: declared {csv_trainee!r} ≠ podium {pod_trainee!r}")
                pod_match = pod_match.iloc[0:0]

        if not pod_match.empty:
            pod_row = pod_match.iloc[0]
            trainee = pod_row["trainee_name"]
            time_val = pod_row["time"] if pd.notna(pod_row["time"]) else csv_time
        else:
            # Stats fallback for canonical name (e.g. SwordResolve / Mayano Top Gun)
            stat_self = stats_df[stats_df["ign"].isin(ign_candidates)]
            if "is_user" in stats_df.columns and stats_df["is_user"].any():
                stat_self_user = stat_self[stat_self["is_user"] == True]
                if not stat_self_user.empty:
                    stat_self = stat_self_user
            stat_name = stat_self.iloc[0]["name"] if not stat_self.empty else None
            if stat_name and pd.notna(stat_name):
                trainee = stat_name
                if trainee != csv_trainee:
                    print(f"  Canonicalized {ign}: CSV={csv_trainee!r} -> stats={trainee!r}")
            else:
                trainee = csv_trainee
            time_val = csv_time
            print(f"  NOTE {ign}: no podium row for {trainee} (using CSV time={csv_time!r})")

        if trainee in claimed_umas:
            print(f"  SKIP {ign}: {trainee} already claimed (duplicate or post-canonicalization collision)")
            continue
        claimed_umas.add(trainee)

        has_user_flag = stats_df["is_user"].any()
        if has_user_flag:
            stat_row = stats_df[
                (stats_df["ign"].isin(ign_candidates))
                & (stats_df["name"] == trainee)
                & (stats_df["is_user"] == True)
            ]
            if stat_row.empty:
                stat_row = stats_df[
                    (stats_df["ign"].isin(ign_candidates)) & (stats_df["is_user"] == True)
                ]
        else:
            stat_row = stats_df[
                (stats_df["ign"].isin(ign_candidates)) & (stats_df["name"] == trainee)
            ]
            if stat_row.empty:
                stat_row = stats_df[stats_df["ign"].isin(ign_candidates)]

        if not stat_row.empty:
            s = stat_row.iloc[0]
            stats = {
                "speed": int(s["Speed"]),
                "stamina": int(s["Stamina"]),
                "power": int(s["Power"]),
                "guts": int(s["Guts"]),
                "wit": int(s["Wit"]),
            }
        else:
            print(f"  WARN {ign}: no stats found, using zeroes")
            stats = {"speed": 0, "stamina": 0, "power": 0, "guts": 0, "wit": 0}

        images_needed.add(trainee)

        slides.append({
            "ign": ign,
            "trainee_name": trainee,
            "uma_image": f"umas/{trainee}.png",
            "time": time_val,
            "result": "1st",
            "quote": quote,
            "stats": stats,
        })

    overrides, patches = load_overrides(args.event, project_root)
    for ov in overrides:
        ign = ov["ign"]
        trainee = ov["trainee_name"]

        csv_row = finals_df[finals_df[COL_IGN] == ign]
        csv_quote = ""
        csv_time = ""
        if not csv_row.empty:
            cr = csv_row.iloc[0]
            if pd.notna(cr[COL_QUOTE]):
                csv_quote = cr[COL_QUOTE]
            if COL_WINNER_TIME in csv_row.columns and pd.notna(cr[COL_WINNER_TIME]):
                csv_time = cr[COL_WINNER_TIME]
        if trainee in claimed_umas:
            print(f"  OVERRIDE SKIP {ign}: {trainee} already claimed by auto-generated slide")
            continue
        claimed_umas.add(trainee)

        ign_candidates = [ign]
        alias = resolve_alias(ign)
        if alias:
            ign_candidates.append(alias)

        stat_row = stats_df[
            (stats_df["ign"].isin(ign_candidates)) & (stats_df["name"] == trainee)
        ]
        if stat_row.empty:
            stat_row = stats_df[stats_df["ign"].isin(ign_candidates)]

        if not stat_row.empty:
            s = stat_row.iloc[0]
            stats = {
                "speed": int(s["Speed"]),
                "stamina": int(s["Stamina"]),
                "power": int(s["Power"]),
                "guts": int(s["Guts"]),
                "wit": int(s["Wit"]),
            }
        else:
            print(f"  OVERRIDE WARN {ign}: no stats found, using zeroes")
            stats = {"speed": 0, "stamina": 0, "power": 0, "guts": 0, "wit": 0}

        images_needed.add(trainee)
        slides.append({
            "ign": ign,
            "trainee_name": trainee,
            "uma_image": f"umas/{trainee}.png",
            "time": ov.get("time") or csv_time,
            "result": "1st",
            "quote": ov.get("quote") or csv_quote,
            "stats": stats,
        })
        reason = ov.get("reason", "manual override")
        print(f"  OVERRIDE {ign} -> {trainee} ({reason})")

    # Apply field patches (curated quotes, manual time fixes, etc.)
    PATCHABLE_FIELDS = {"time", "quote", "stats", "trainee_name", "uma_image", "result", "full_art_compact", "full_art_image"}
    slides_by_ign = {s["ign"]: s for s in slides}
    for patch in patches:
        ign = patch.get("ign")
        target = slides_by_ign.get(ign)
        if not target:
            print(f"  PATCH SKIP {ign}: no matching slide")
            continue
        applied = []
        for k, v in patch.items():
            if k == "ign" or k not in PATCHABLE_FIELDS:
                continue
            target[k] = v
            applied.append(k)
        if applied:
            print(f"  PATCH {ign}: {', '.join(applied)}")

    for slide_entry in slides:
        trainee = slide_entry["trainee_name"]

        if trainee in ALT_ART:
            alt_path = project_root / "public" / "umas" / ALT_ART[trainee]
            if alt_path.exists():
                slide_entry["full_art_image"] = f"umas/{ALT_ART[trainee]}"
                print(f"  Full art assigned (alt): {trainee} -> {ALT_ART[trainee]}")
                continue

        base_name = re.sub(r"\[.*?\]\s*", "", trainee).strip()
        full_art_name = base_name.replace(" ", "_") + "_(Race).png"
        full_art_path = project_root / "public" / "umas" / full_art_name
        if full_art_path.exists():
            if base_name in DEFAULT_COSTUME and DEFAULT_COSTUME[base_name] != trainee:
                continue
            slide_entry["full_art_image"] = f"umas/{full_art_name}"
            print(f"  Full art assigned: {trainee} -> {full_art_name}")

    print(f"\nGenerated {len(slides)} slides")

    data_dir = project_root / "src" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    event_data = {
        "event": {
            "name": cfg["name"],
            "id": args.event,
            "icon": cfg["icon"],
            "theme": cfg.get("theme", "default"),
            "distance": cfg["distance"],
            "surface": cfg["surface"],
            "track": cfg["track"],
        },
        "slides": slides,
    }

    json_path = data_dir / f"slides-{args.event.lower()}.json"
    with open(json_path, "w") as f:
        json.dump(event_data, f, indent=2, ensure_ascii=False)
    print(f"Wrote {json_path}")

    index_path = data_dir / "index.json"
    if index_path.exists():
        with open(index_path) as f:
            index = json.load(f)
    else:
        index = {"events": []}

    existing = {e["id"] for e in index["events"]}
    entry = {
        "id": args.event,
        "name": cfg["name"],
        "icon": cfg["icon"],
        "file": f"slides-{args.event.lower()}.json",
        "slideCount": len(slides),
    }
    if args.event in existing:
        index["events"] = [entry if e["id"] == args.event else e for e in index["events"]]
    else:
        index["events"].append(entry)

    def _sort_key(e):
        eid = e["id"]
        if eid.startswith("CM") and eid[2:].isdigit():
            return (0, int(eid[2:]))
        return (1, eid)

    index["events"].sort(key=_sort_key)
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    print(f"Updated {index_path}")

    # --- Write winners JSON and Markdown ---
    out_dir = project_root / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    base_name_fn = lambda t: re.sub(r"\[.*?\]\s*", "", t).strip()

    winners = []
    for s in slides:
        winners.append({
            "ign": s["ign"],
            "trainee_name": s["trainee_name"],
            "base_name": base_name_fn(s["trainee_name"]),
            "time": s["time"],
            "stats": s["stats"],
            "quote": s["quote"],
        })

    winners_json_path = out_dir / f"winners-{args.event.lower()}.json"
    with open(winners_json_path, "w") as f:
        json.dump({
            "event": args.event,
            "name": cfg["name"],
            "track": cfg["track"],
            "winners": winners,
        }, f, indent=2, ensure_ascii=False)
    print(f"Wrote {winners_json_path}")

    winners_md_path = out_dir / f"winners-{args.event.lower()}.md"
    with open(winners_md_path, "w") as f:
        f.write(f"# {cfg['name']} ({args.event}) — Oshi's Champion Awardees\n\n")
        f.write(f"**Track:** {cfg['track']}  \n")
        f.write(f"**Winners:** {len(winners)}\n\n")
        f.write("---\n\n")
        for i, w in enumerate(winners, 1):
            total = sum(w["stats"].values())
            f.write(f"### {i}. {w['ign']}\n\n")
            f.write(f"**Uma:** {w['trainee_name']}  \n")
            f.write(f"**Time:** {w['time']}  \n")
            f.write(f"**Stats:** {w['stats']['speed']} / {w['stats']['stamina']} / {w['stats']['power']} / {w['stats']['guts']} / {w['stats']['wit']} (Total: {total})  \n")
            if w["quote"]:
                f.write(f"\n> {w['quote']}\n")
            f.write("\n")
    print(f"Wrote {winners_md_path}")

    umas_out = project_root / "public" / "umas"
    umas_out.mkdir(parents=True, exist_ok=True)
    if umas_dir:
        copied = 0
        for name in images_needed:
            src = umas_dir / f"{name}.png"
            dst = umas_out / f"{name}.png"
            if src.exists():
                shutil.copy2(src, dst)
                copied += 1
            else:
                print(f"  WARN image not found: {src.name}")
        print(f"Copied {copied}/{len(images_needed)} images to {umas_out}")
    else:
        missing = [n for n in images_needed if not (umas_out / f"{n}.png").exists()]
        if missing:
            print(f"  WARN {len(missing)} images not in public/umas/: {', '.join(missing)}")
        print(f"Skipped image copy (local mode, no --repo source)")

    # Normalize uma image filenames so the browser can find them:
    #   1. URL-decode percent-escapes (wiki downloads keep %28/%29 in names)
    #   2. Apply NFC unicode normalization (macOS Finder sometimes stores NFD)
    renamed = 0
    for entry in umas_out.iterdir():
        if not entry.is_file():
            continue
        clean = unicodedata.normalize("NFC", urllib.parse.unquote(entry.name))
        if clean != entry.name:
            entry.rename(entry.with_name(clean))
            renamed += 1
    if renamed:
        print(f"Normalized {renamed} filename(s) (URL-decode + NFC) in {umas_out}")


if __name__ == "__main__":
    main()
