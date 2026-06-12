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
        "finals_csv": "events/cm9/data/sheet_cache_merged.csv",
        "statsheet": "events/cm9/data/statsheet.parquet",
        "podium": "events/cm9/data/podium.parquet",
    },
    "CM10": {
        "name": "Aquarius Cup",
        "icon": "aquarius_icon.png",
        "theme": "uma",
        "distance": "Mile",
        "surface": "Dirt",
        "track": "Tokyo Dirt 1600m",
        "finals_csv": "events/cm10/data/sheet_cache_merged.csv",
        "statsheet": "events/cm10/data/statsheet.parquet",
        "podium": "events/cm10/data/podium.parquet",
    },
    "CM11": {
        "name": "Pisces Cup",
        "icon": "pisces_icon.png",
        "theme": "uma",
        "distance": "Long",
        "surface": "Turf",
        "track": "Hanshin Turf 3200m",
        "finals_csv": "events/cm11/data/sheet_cache_merged.csv",
        "statsheet": "events/cm11/data/statsheet.parquet",
        "podium": "events/cm11/data/podium.parquet",
    },
    "CM12": {
        "name": "Aries Cup",
        "icon": "aries_icon.png",
        "theme": "uma",
        "distance": "Medium",
        "surface": "Turf",
        "track": "Nakayama Turf 2000m",
        "finals_csv": "events/cm12/data/sheet_cache_merged.csv",
        "statsheet": "events/cm12/data/statsheet.parquet",
        "podium": "events/cm12/data/podium.parquet",
    },
    "CM13": {
        "name": "2nd Taurus Cup",
        "icon": "taurus_icon.png",
        "theme": "uma",
        "distance": "Medium",
        "surface": "Turf",
        "track": "Tokyo Turf 2400m",
        "finals_csv": "events/cm13/data/sheet_cache_merged.csv",
        "statsheet": "events/cm13/data/statsheet.parquet",
        "podium": "events/cm13/data/podium.parquet",
        "schema": "v2",
    },
    "CM14": {
        "name": "Gemini Cup",
        "icon": "gemini_icon.png",
        "theme": "uma",
        "distance": "Mile",
        "surface": "Turf",
        "track": "Tokyo Turf 1600m",
        "finals_csv": "events/cm14/data/sheet_cache_merged.csv",
        "statsheet": "events/cm14/data/statsheet.parquet",
        "podium": "events/cm14/data/podium.parquet",
        "schema": "v2",
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
    "Fuji Kiseki": "[Shooting Star Revue] Fuji Kiseki",
    "Biwa Hayahide": "[pf. Winning Equation...] Biwa Hayahide",
    "El Condor Pasa": "[El☆Número 1] El Condor Pasa",
    "Mayano Top Gun": "[Scramble☆Zone] Mayano Top Gun",
    "Special Week": "[Special Dreamer] Special Week",
    "Symboli Rudolf": "[Emperor's Path] Symboli Rudolf",
    "Tokai Teio": "[Peak Joy] Tokai Teio",
    "Curren Chan": "[Fille Éclair] Curren Chan",
}

ALT_ART = {
    "[Vampire Makeover!] Rice Shower": "Rice_Shower_(Alt).png",
    "[Succès Étoilé] Fuji Kiseki": "Fuji_Kiseki_(Alt).png",
    "[Precise Chocolatier] Eishin Flash": "Eishin_Flash_(Alt).png",
    "[Rouge Caroler] Biwa Hayahide": "Biwa_Hayahide_(Alt).png",
    "[Archer by Moonlight] Symboli Rudolf": "Symboli_Rudolf_(Alt).png",
    "[Sunlight Bouquet] Mayano Top Gun": "Mayano_Top_Gun_(Alt).png",
    "[Hopp'n♪Happy Heart] Special Week": "Special_Week_(Alt).png",
    "[Kukulkan Warrior] El Condor Pasa": "El_Condor_Pasa_(Alt).png",
    "[Chiffon-Wrapped Mummy] Super Creek": "Super_Creek_(Alt).png",
    "[Beyond the Horizon] Tokai Teio": "Tokai_Teio_(Alt).png",
    "[Ma Chérie of the New Moon] Curren Chan": "Curren_Chan_(Alt).png",
}

# Maps survey IGN -> trainer_name as it appears in the podium/stats parquet.
# Use when the player submitted their data under a different name and fuzzy
# matching would fail (case-insensitive lookup).
IGN_ALIASES = {
    "mahoneyos": "Mitchell",
}


def resolve_alias(ign):
    """Return the aliased trainer name for an IGN, or None."""
    return IGN_ALIASES.get(str(ign).lower())


def _clean_quote(text):
    """Strip surrounding quote characters a user may have wrapped their quote in.

    The slide component already renders enclosing quotation marks, so a quote
    submitted as ``"like this"`` would otherwise display double-quoted. Only the
    wrapping pair is removed, and only when the inner text doesn't itself contain
    that quote char (so legit quotes like ``"a" and "b"`` are left intact).
    """
    if not text:
        return ""
    s = str(text).strip()
    pairs = {'"': '"', "'": "'", "\u201c": "\u201d", "\u2018": "\u2019"}
    while len(s) >= 2:
        for lq, rq in pairs.items():
            if s[0] == lq and s[-1] == rq and lq not in s[1:-1] and rq not in s[1:-1]:
                s = s[1:-1].strip()
                break
        else:
            break
    return s


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

    Exclusion entries: list of {trainee_name?, ign?, reason?}. An auto-derived
    award is dropped when its winner-name matches an excluded `trainee_name`
    (case-insensitive) or its IGN matches an excluded `ign`. Use for meta /
    "free-win" picks that win en masse and aren't genuine oshi achievements.
    """
    path = project_root / "overrides" / f"{event_id.lower()}.json"
    if not path.exists():
        return [], [], []
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, list):
        return data, [], []
    return data.get("overrides", []), data.get("patches", []), data.get("exclusions", [])


COL_OSHI_QUOTE_V2 = 'Optional - Finals - Winner - Oshi Award Quote (in case you end up winning one)'

# CM14+ renamed the per-winner columns from "Winner" to "Own Winner" (the form
# now also collects "Opponent Winner" data). Map those variants back onto the
# canonical names the rest of the pipeline expects so v2 handling is unchanged.
V2_COLUMN_ALIASES = {
    'Optional - Finals - Own Winner - Oshi Award Quote (in case you end up winning one)': COL_OSHI_QUOTE_V2,
    'Optional - Finals - Own Winner - Screenshot - Stat Screen (First Image)': COL_STAT_UPLOAD_1,
    'Optional - Finals - Own Winner - Screenshot - Stat Screen (Second Image)': COL_STAT_UPLOAD_2,
}


def canonicalize_v2_columns(df):
    """Rename CM14+ 'Own Winner' columns to the canonical 'Winner' names.

    Only renames when the source column exists and the canonical target isn't
    already present, so it's safe to call on any event's CSV (idempotent).
    """
    rename = {
        src: dst
        for src, dst in V2_COLUMN_ALIASES.items()
        if src in df.columns and dst not in df.columns
    }
    if rename:
        df = df.rename(columns=rename)
        print(f"[v2 columns] Canonicalized {len(rename)} 'Own Winner' column(s): {sorted(rename.values())}")
    return df


def _normalize_v2(finals_df, podium_df, stats_df=None):
    """CM13+ form schema dropped 'Finals - Winner - Name', winner-time, and the
    oshi flag. Reconstruct v1-equivalent columns from CSV + podium + statsheet
    so the rest of the pipeline runs unchanged.

    Winning ace + time resolution order per CSV IGN:
      1. Podium parquet `is_user=True, placement=1` matched to IGN via exact /
         alias / fuzzy trainer_name lookup.
      2. (Rescue) Statsheet parquet `is_user=True, ign=IGN` — the stat-screen
         OCR independently confirms the submitter and their declared trainee.
         This catches cases where the in-game name on the podium screenshot
         differs from the IGN typed into the form (so podium OCR set
         is_user=False on the actual winning row). Time is then pulled from
         podium `placement=1, trainee_name=name` if uniquely available.

    Oshi flag: 'Yes' iff the v2 oshi-quote field is non-empty (deliberate opt-in).
    Quote: copied from the v2 quote column into the canonical COL_QUOTE.
    """
    user_wins = podium_df[(podium_df["is_user"] == True) & (podium_df["placement"] == 1)]
    by_trainer = {}
    consumed_rowids = set()
    for _, r in user_wins.iterrows():
        k = str(r["trainer_name"]).strip().lower()
        if k and k not in by_trainer:
            by_trainer[k] = (r["trainee_name"], r["time"] if pd.notna(r["time"]) else "")
            if pd.notna(r["row_id"]):
                consumed_rowids.add(int(r["row_id"]))

    # Stat-verified rescue map: ign -> trainee_name from statsheet's own OCR.
    # Statsheet OCR matches the stat-screen header against the CSV IGN
    # directly, so is_user=True there is independent ground truth even when
    # the podium OCR couldn't link the post-race trainer name back to the IGN.
    stat_rescue = {}
    if stats_df is not None and "is_user" in stats_df.columns and "ign" in stats_df.columns:
        verified = stats_df[stats_df["is_user"] == True]
        if "name" in verified.columns:
            grouped = verified.groupby(verified["ign"].astype(str).str.strip().str.lower())["name"]
            for ign_l, names in grouped:
                uniq = {str(n) for n in names if pd.notna(n) and str(n).strip()}
                if len(uniq) == 1:
                    stat_rescue[ign_l] = next(iter(uniq))

    # Time-from-podium lookup keyed by trainee_name. We accept any placement=1
    # row even where is_user=False since the rescue is already gated on the
    # statsheet match — this keeps the pool uniqueness rule honest.
    podium_p1 = podium_df[podium_df["placement"] == 1]

    def podium_proof(trainee, used_rowids):
        """Return (time, claimed_rowid, found) for an unclaimed placement=1
        podium row matching `trainee`. `found=True` means at least one
        unclaimed row exists (proof the win actually occurred). Time + rowid
        are only returned when exactly one unclaimed candidate remains —
        otherwise the win is real but unattributable, so leave time blank."""
        rows = podium_p1[
            (podium_p1["trainee_name"] == trainee)
            & (~podium_p1["row_id"].isin(used_rowids))
        ]
        if rows.empty:
            return "", None, False
        timed = rows[rows["time"].notna()]
        if len(timed) == 1:
            return str(timed.iloc[0]["time"]), int(timed.iloc[0]["row_id"]), True
        return "", None, True

    def lookup(ign):
        ign_l = str(ign).strip().lower()
        alias = resolve_alias(ign)
        alias_l = alias.lower() if alias else None
        if ign_l in by_trainer:
            return (*by_trainer[ign_l], "podium")
        if alias_l and alias_l in by_trainer:
            return (*by_trainer[alias_l], "podium")
        for k, v in by_trainer.items():
            if (
                k.startswith(ign_l[:3])
                or ign_l.startswith(k[:3])
                or k in ign_l
                or ign_l in k
            ):
                return (*v, "podium")
        return (None, None, None)

    out = finals_df.copy()
    names, times = [], []
    rescued_igns = []
    skipped_no_podium = []
    # Seed rescue's used_rowids with rows already claimed by pass-1 podium
    # matches, so a rescued IGN never inherits another confirmed winner's time.
    used_rowids = set(consumed_rowids)
    for ign in out[COL_IGN]:
        n, t, src = lookup(ign)
        if not n:
            ign_l = str(ign).strip().lower()
            if ign_l in stat_rescue:
                candidate = stat_rescue[ign_l]
                rescued_t, claimed_rowid, has_podium = podium_proof(candidate, used_rowids)
                # Two-part verification: statsheet says X won Y, AND there
                # exists at least one unclaimed placement=1 podium row for Y
                # (the actual race-result screenshot, not someone else's
                # already-claimed win). If exactly one unclaimed row remains
                # we attribute its time; otherwise leave time blank but still
                # accept the rescue so uniqueness checks include this claim.
                if has_podium:
                    if claimed_rowid is not None:
                        used_rowids.add(claimed_rowid)
                    n, t, src = candidate, rescued_t, "statsheet"
                    rescued_igns.append((ign, n, t or "(no time)"))
                else:
                    skipped_no_podium.append((ign, candidate))
        names.append(n)
        times.append(t)
    out[COL_WINNER_NAME] = names
    out[COL_WINNER_TIME] = times

    if COL_OSHI_QUOTE_V2 in out.columns:
        quote_series = out[COL_OSHI_QUOTE_V2].fillna("").astype(str).str.strip()
    else:
        quote_series = pd.Series([""] * len(out), index=out.index)
    out[COL_QUOTE] = quote_series
    out[COL_OSHI] = quote_series.apply(lambda q: "Yes" if q else "No")

    print(f"[v2 normalize] Mapped {sum(1 for n in names if n)}/{len(names)} CSV rows to a winning ace")
    print(f"[v2 normalize] Statsheet rescue: {len(rescued_igns)} ign(s) recovered via stat-screen OCR")
    for ign, n, t in rescued_igns:
        print(f"  rescued: {ign} -> {n} (time {t})")
    if skipped_no_podium:
        print(f"[v2 normalize] Skipped {len(skipped_no_podium)} statsheet-only candidate(s) with no unclaimed placement=1 podium row:")
        for ign, n in skipped_no_podium:
            print(f"  unverified: {ign} -> {n}")
    print(f"[v2 normalize] Oshi-quote-claim signal present on {(quote_series != '').sum()} rows")
    return out


def _csv_only_preview(finals_df):
    """Print the strict candidate pool + oshi-claiming uniques without touching parquets."""
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
    pool = finals_df[pool_filter & finals_df[COL_WINNER_NAME].notna()].copy()
    print(f"Strict candidate pool (Graded/A-Finals/1st/SubmitPodium/SubmitStat): {len(pool)}")

    counts = pool[COL_WINNER_NAME].value_counts()
    uniques = set(counts[counts == 1].index)
    dupes = counts[counts > 1]
    print(f"Unique declared winners: {len(uniques)}")
    if len(dupes):
        print(f"Contested umas (>1 declarant in pool): {len(dupes)}")
        for name, n in dupes.items():
            print(f"  [{n}x] {name}")

    oshi_unique = pool[
        (pool[COL_OSHI] == "Yes")
        & pool[COL_WINNER_NAME].isin(uniques)
    ]
    print(f"\nOshi-claiming unique winners: {len(oshi_unique)}\n")
    for _, r in oshi_unique.iterrows():
        ign = r[COL_IGN]
        trainee = r[COL_WINNER_NAME]
        time_val = r[COL_WINNER_TIME] if COL_WINNER_TIME in r and pd.notna(r[COL_WINNER_TIME]) else ""
        print(f"  {ign:25s}  {trainee}  ({time_val or '—'})")

    non_oshi_unique = pool[
        (pool[COL_OSHI] != "Yes")
        & pool[COL_WINNER_NAME].isin(uniques)
    ]
    if len(non_oshi_unique):
        print(f"\nUnique winners NOT claiming oshi ({len(non_oshi_unique)}) — would be excluded:")
        for _, r in non_oshi_unique.iterrows():
            print(f"  {r[COL_IGN]:25s}  {r[COL_WINNER_NAME]}")


def main():
    parser = argparse.ArgumentParser(description="Generate oshi award slide data")
    parser.add_argument("--repo", help="Path to Umamusume_Virgo_Cup_Dashboard repo (optional for local events)")
    parser.add_argument("--event", required=True, choices=EVENT_CONFIG.keys(), help="Event ID")
    parser.add_argument("--csv", help="Override path to finals CSV (useful when parquets aren't ready yet)")
    parser.add_argument("--csv-only", action="store_true", help="CSV-only preview: print candidate pool & oshi list, then exit (no parquets, no slides)")
    args = parser.parse_args()

    cfg = EVENT_CONFIG[args.event]
    project_root = Path(__file__).resolve().parent.parent

    if cfg.get("local"):
        data_base = project_root / "src" / "data"
        umas_dir = None
    else:
        if not args.repo and not args.csv:
            parser.error(f"--repo is required for {args.event} (or pass --csv for csv-only previews)")
        data_base = Path(args.repo).resolve() if args.repo else project_root
        umas_dir = (data_base / "assets" / "umas") if args.repo else None

    csv_path = Path(args.csv).expanduser().resolve() if args.csv else (data_base / cfg["finals_csv"])
    finals_df = pd.read_csv(csv_path)
    if cfg.get("schema") == "v2":
        finals_df = canonicalize_v2_columns(finals_df)

    if args.csv_only:
        print(f"Loaded {len(finals_df)} CSV rows from {csv_path}")
        _csv_only_preview(finals_df)
        return

    podium_df = pd.read_parquet(data_base / cfg["podium"])
    stats_df = pd.read_parquet(data_base / cfg["statsheet"])

    print(f"Loaded {len(finals_df)} CSV rows, {len(podium_df)} podium rows, {len(stats_df)} stat rows")

    if cfg.get("schema") == "v2":
        finals_df = _normalize_v2(finals_df, podium_df, stats_df)

    # --- Award rule: unique among OSHI claimants -------------------------
    # The "Oshi's Champion" award goes to a player iff they are the SOLE
    # person who both (a) claimed a given uma as their oshi (oshi=Yes) and
    # (b) won finals (1st, Graded) with it. Uniqueness is measured over the
    # oshi-claim universe — every 1st-place Graded oshi=Yes claim with a
    # derived winner-name, across BOTH A and B finals — so a B-finals
    # oshi-claimant still contests an A-finals award, while non-oshi
    # co-winners never dilute it. Winning with a popular/meta uma is common;
    # this award is about the oshi claim, not raw race results.
    graded = finals_df[COL_LEAGUE].astype(str).str.startswith(LEAGUE_GRADED_PREFIX)
    first = finals_df[COL_RESULT] == "1st"
    named = finals_df[COL_WINNER_NAME].notna()
    oshi_yes = finals_df[COL_OSHI] == "Yes"

    claim_universe = finals_df[graded & first & named & oshi_yes]
    claim_counts = claim_universe[COL_WINNER_NAME].value_counts()
    unique_winner_names = set(claim_counts[claim_counts == 1].index)
    print(f"Oshi-claim universe (1st/Graded/oshi=Yes, A+B finals): {len(claim_universe)}")
    contested = claim_counts[claim_counts > 1]
    print(f"Sole-claimant umas: {len(unique_winner_names)} | contested (no award): {len(contested)}")

    # Hidden-collision guard: an oshi=Yes claim whose winner-name derivation
    # failed (null) is invisible to the count above. Recover its uma from the
    # player's own stat-screen / 1st-place podium (is_user=True ground truth)
    # and demote any award it actually contests.
    own_stats = stats_df[stats_df["is_user"] == True] if "is_user" in stats_df.columns else stats_df.iloc[0:0]
    own_wins = (
        podium_df[(podium_df["is_user"] == True) & (podium_df["placement"] == 1)]
        if "is_user" in podium_df.columns else podium_df.iloc[0:0]
    )
    null_oshi = finals_df[graded & first & oshi_yes & finals_df[COL_WINNER_NAME].isna()]
    for _, urow in null_oshi.iterrows():
        uign = str(urow[COL_IGN])
        ualias = resolve_alias(uign)
        cands = {uign.lower()} | ({ualias.lower()} if ualias else set())
        recovered = set()
        for s in own_stats.itertuples():
            if str(s.ign).lower() in cands and pd.notna(s.name):
                recovered.add(str(s.name).strip())
        for p in own_wins.itertuples():
            if str(p.trainer_name).lower() in cands and pd.notna(p.trainee_name):
                recovered.add(str(p.trainee_name).strip())
        for nm in recovered:
            if nm in unique_winner_names:
                unique_winner_names.discard(nm)
                print(f"  COLLISION: '{nm}' also oshi-claimed by {uign} "
                      f"(winner-name derivation failed) — no award")

    # Award pool: the sole claimant must also clear the full evidentiary bar —
    # A-Finals + podium screenshot + stat screenshot.
    isA = (finals_df[COL_FINALS_GROUP] == "A Finals") if COL_FINALS_GROUP in finals_df.columns else pd.Series(True, index=finals_df.index)
    if COL_STAT_UPLOAD_2 in finals_df.columns:
        stat_ok = finals_df[COL_STAT_UPLOAD_1].notna() | finals_df[COL_STAT_UPLOAD_2].notna()
    else:
        stat_ok = finals_df[COL_STAT_UPLOAD_1].notna()
    award_filter = graded & first & named & oshi_yes & isA & finals_df[COL_PODIUM_UPLOAD].notna() & stat_ok
    award_pool = finals_df[award_filter].copy()

    # Manual exclusions (meta / free-win picks that win en masse).
    overrides, patches, exclusions = load_overrides(args.event, project_root)
    excluded_names = {str(e.get("trainee_name", "")).strip().lower() for e in exclusions if e.get("trainee_name")}
    excluded_igns = {str(e.get("ign", "")).strip().lower() for e in exclusions if e.get("ign")}

    oshi_unique = award_pool[award_pool[COL_WINNER_NAME].isin(unique_winner_names)].copy()
    if excluded_names or excluded_igns:
        drop = (
            oshi_unique[COL_WINNER_NAME].astype(str).str.strip().str.lower().isin(excluded_names)
            | oshi_unique[COL_IGN].astype(str).str.strip().str.lower().isin(excluded_igns)
        )
        for _, r in oshi_unique[drop].iterrows():
            print(f"  EXCLUDED {r[COL_IGN]} -> {r[COL_WINNER_NAME]} (manual exclusion)")
        oshi_unique = oshi_unique[~drop]
    print(f"Oshi-claiming unique winners: {len(oshi_unique)}")

    # Podium reference (for time lookup + diagnostics; no longer drives uniqueness)
    race_winners = podium_df[podium_df["placement"] == 1]

    slides = []
    images_needed = set()
    claimed_umas = set()

    for _, row in oshi_unique.iterrows():
        ign = row[COL_IGN]
        csv_trainee = row[COL_WINNER_NAME]
        quote = _clean_quote(row[COL_QUOTE]) if pd.notna(row[COL_QUOTE]) else ""
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

    for ov in overrides:
        ign = ov["ign"]
        trainee = ov["trainee_name"]

        csv_row = finals_df[finals_df[COL_IGN] == ign]
        csv_quote = ""
        csv_time = ""
        if not csv_row.empty:
            cr = csv_row.iloc[0]
            if pd.notna(cr[COL_QUOTE]):
                csv_quote = _clean_quote(cr[COL_QUOTE])
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

        # Explicit stats win (used when the statsheet ign would expose a real
        # name, or when no statsheet row exists). Otherwise look up by ign+name.
        if isinstance(ov.get("stats"), dict):
            stats = {k: int(ov["stats"].get(k, 0)) for k in ("speed", "stamina", "power", "guts", "wit")}
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
