#!/usr/bin/env python3
"""
Preprocess Umamusume dashboard data into slide JSON for the Preact viewer.

Usage:
    python3 scripts/preprocess.py --repo ../Umamusume_Virgo_Cup_Dashboard --event CM10
"""

import argparse
import json
import os
import re
import shutil
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
}

COL_IGN = "Unique display name"
COL_OSHI = 'Did you build an "oshi"/niche uma ace this CM?'
COL_QUOTE = 'Optional - Quote in case you win an "Oshi award" this CM to be used in the award'
COL_RESULT = "Finals result?"

DEFAULT_COSTUME = {
    "Rice Shower": "[Rosy Dreams] Rice Shower",
}

ALT_ART = {
    "[Vampire Makeover!] Rice Shower": "Rice_Shower_(Alt).png",
}


def main():
    parser = argparse.ArgumentParser(description="Generate oshi award slide data")
    parser.add_argument("--repo", required=True, help="Path to Umamusume_Virgo_Cup_Dashboard repo")
    parser.add_argument("--event", required=True, choices=EVENT_CONFIG.keys(), help="Event ID")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    cfg = EVENT_CONFIG[args.event]
    project_root = Path(__file__).resolve().parent.parent

    finals_df = pd.read_csv(repo / cfg["finals_csv"])
    podium_df = pd.read_parquet(repo / cfg["podium"])
    stats_df = pd.read_parquet(repo / cfg["statsheet"])
    umas_dir = repo / "assets" / "umas"

    print(f"Loaded {len(finals_df)} CSV rows, {len(podium_df)} podium rows, {len(stats_df)} stat rows")

    oshi_first = finals_df[
        (finals_df[COL_OSHI] == "Yes") & (finals_df[COL_RESULT] == "1st")
    ]
    print(f"Oshi 1st-place winners in CSV: {len(oshi_first)}")

    race_winners = podium_df[podium_df["placement"] == 1]
    uma_win_counts = race_winners["trainee_name"].value_counts()
    unique_umas = set(uma_win_counts[uma_win_counts == 1].index)
    print(f"Unique winning umas (appeared exactly once): {len(unique_umas)}")

    slides = []
    images_needed = set()
    claimed_umas = set()

    for _, row in oshi_first.iterrows():
        ign = row[COL_IGN]
        quote = row[COL_QUOTE] if pd.notna(row[COL_QUOTE]) else ""

        player_wins = race_winners[race_winners["trainer_name"] == ign]
        if player_wins.empty:
            stat_match = stats_df[(stats_df["ign"] == ign) & (stats_df["is_user"] == True)]
            if stat_match.empty:
                stat_match = stats_df[stats_df["ign"] == ign]
            if not stat_match.empty:
                candidate = stat_match.iloc[0]["name"]
                player_wins = race_winners[race_winners["trainee_name"] == candidate]
                if not player_wins.empty:
                    print(f"  Resolved {ign} via stats fallback -> {candidate}")
            if player_wins.empty:
                print(f"  SKIP {ign}: no podium win found")
                continue

        win = player_wins.iloc[0]
        trainee = win["trainee_name"]
        time_val = win["time"] if pd.notna(win["time"]) else ""

        if trainee not in unique_umas:
            print(f"  SKIP {ign}: {trainee} not unique ({uma_win_counts.get(trainee, 0)} wins)")
            continue

        if trainee in claimed_umas:
            print(f"  SKIP {ign}: {trainee} already claimed by another player")
            continue
        claimed_umas.add(trainee)

        has_user_flag = stats_df["is_user"].any()
        if has_user_flag:
            stat_row = stats_df[
                (stats_df["ign"] == ign)
                & (stats_df["name"] == trainee)
                & (stats_df["is_user"] == True)
            ]
            if stat_row.empty:
                stat_row = stats_df[
                    (stats_df["ign"] == ign) & (stats_df["is_user"] == True)
                ]
        else:
            stat_row = stats_df[
                (stats_df["ign"] == ign) & (stats_df["name"] == trainee)
            ]
            if stat_row.empty:
                stat_row = stats_df[stats_df["ign"] == ign]

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

    index["events"].sort(key=lambda e: e["id"])
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


if __name__ == "__main__":
    main()
