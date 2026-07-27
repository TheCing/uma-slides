#!/usr/bin/env python3
"""Fetch missing TOC thumbnail images from gametora.

The TOC portrait uses a per-costume headshot at ``public/<uma_image>`` keyed by
the full ``[Costume] Name`` trainee name. gametora serves the matching 512x512
transparent character render at::

    https://gametora.com/images/umamusume/characters/chara_stand_{chara}_{card}.png

where ``card`` is the umamusume card id (text_data category 4 index in the
global master DB) and ``chara = card // 100``.

Usage:
    python scripts/fetch_thumbs.py --event CM14          # one event
    python scripts/fetch_thumbs.py --all                 # every slides-*.json
    python scripts/fetch_thumbs.py --all --force         # re-download existing
"""
import argparse
import json
import sqlite3
import sys
import time
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "src" / "data"
PUBLIC_DIR = PROJECT_ROOT / "public"
DEFAULT_MDB = Path.home() / "Dev" / "uma-tools-1" / "docs" / "master.mdb"
GT_URL = "https://gametora.com/images/umamusume/characters/chara_stand_{chara}_{card}.png"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


def resolve_card_id(cur, trainee_name):
    """Return the gametora card id for an exact '[Costume] Name' string."""
    row = cur.execute(
        'SELECT "index" FROM text_data WHERE category=4 AND text=?',
        (trainee_name,),
    ).fetchone()
    return row[0] if row else None


def download(card_id, dest):
    chara = card_id // 100
    url = GT_URL.format(chara=chara, card=card_id)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    if not data.startswith(b"\x89PNG"):
        raise ValueError("response is not a PNG")
    dest.write_bytes(data)
    return url, len(data)


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--event", help="Event id, e.g. CM14")
    g.add_argument("--all", action="store_true", help="Process every slides-*.json")
    ap.add_argument("--mdb", default=str(DEFAULT_MDB), help="Path to master-global.mdb")
    ap.add_argument("--force", action="store_true", help="Re-download even if file exists")
    args = ap.parse_args()

    mdb = Path(args.mdb).expanduser()
    if not mdb.exists():
        sys.exit(f"master DB not found: {mdb}")

    if args.all:
        slide_files = sorted(DATA_DIR.glob("slides-*.json"))
    else:
        f = DATA_DIR / f"slides-{args.event.lower()}.json"
        if not f.exists():
            sys.exit(f"slides file not found: {f}")
        slide_files = [f]

    con = sqlite3.connect(mdb)
    cur = con.cursor()

    fetched = skipped = unresolved = failed = 0
    for sf in slide_files:
        data = json.loads(sf.read_text())
        slides = data["slides"] if isinstance(data, dict) else data
        print(f"\n== {sf.name} ({len(slides)} slides) ==")
        for s in slides:
            rel = s.get("uma_image")
            name = s.get("trainee_name")
            if not rel or not name:
                continue
            dest = PUBLIC_DIR / rel
            if dest.exists() and not args.force:
                skipped += 1
                continue
            card = resolve_card_id(cur, name)
            if not card:
                print(f"  ?? UNRESOLVED  {name}")
                unresolved += 1
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                url, size = download(card, dest)
                print(f"  OK {card}  {name}  ({size:,}B)")
                fetched += 1
                time.sleep(0.4)
            except Exception as e:  # noqa: BLE001
                print(f"  !! FAILED {card}  {name}: {e}")
                failed += 1

    con.close()
    print(
        f"\nDone. fetched={fetched} skipped(existing)={skipped} "
        f"unresolved={unresolved} failed={failed}"
    )


if __name__ == "__main__":
    main()
