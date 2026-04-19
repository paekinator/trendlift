"""
prepare_data.py
───────────────
Merges per-country YouTube trending CSV files into a single cleaned CSV:
  data/processed/trending_2026_11c_clean_with_categories.csv

EXPECTED INPUT FILE LAYOUT
───────────────────────────
Put your raw files inside  data/raw/

Supported naming conventions (script tries all of them):
  US_youtube_trending_data.csv   ← Kaggle "Global YouTube Statistics 2023" style
  USvideos.csv                   ← older Kaggle style

Supported column names (script auto-detects):
  video_id        (or: id)
  title
  channelTitle    (or: channel_title)
  publishedAt     (or: publish_time)
  trending_date
  categoryId      (or: category_id)
  view_count      (or: views)
  likes
  comment_count   (or: comments)
  country                        ← injected from filename if missing

If your files have different column names edit COLUMN_MAP below.

CATEGORY JSON FILES (optional)
───────────────────────────────
Some Kaggle versions ship a per-country JSON:
  data/raw/US_category_id.json
If present the script uses it to fill in category names.
If absent it falls back to the built-in YouTube category map.

RUN
───
cd /path/to/your/project          # project root (not backend/)
python backend/scripts/prepare_data.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

# ── Project root (2 levels up from backend/scripts/) ──────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR       = _PROJECT_ROOT / "data" / "raw"
OUT_DIR       = _PROJECT_ROOT / "data" / "processed"
OUT_FILE      = OUT_DIR / "trending_2026_11c_clean_with_categories.csv"

# ── Countries to include (ISO-2 upper-case) ────────────────────────────────────
# Edit this list to match the country files you actually have.
COUNTRIES = ["US", "GB", "CA", "IN", "DE", "FR", "JP", "KR", "BR", "MX", "RU"]

# ── Column name aliases ────────────────────────────────────────────────────────
# Maps canonical name → list of variants that appear in raw files.
# Add entries here if your files use different names.
COLUMN_MAP: dict[str, list[str]] = {
    "video_id":       ["video_id", "id"],
    "title":          ["title"],
    "channelTitle":   ["channelTitle", "channel_title", "channelName"],
    "publishedAt":    ["publishedAt", "publish_time", "published_at"],
    "trending_date":  ["trending_date", "trending_date"],
    "categoryId":     ["categoryId", "category_id"],
    "view_count":     ["view_count", "views", "viewCount"],
    "likes":          ["likes"],
    "comment_count":  ["comment_count", "comments", "commentCount"],
}

# Built-in YouTube category map (fallback when no JSON is present)
_BUILTIN_CATEGORIES: dict[int, str] = {
    1:  "Film & Animation",
    2:  "Autos & Vehicles",
    10: "Music",
    15: "Pets & Animals",
    17: "Sports",
    18: "Short Movies",
    19: "Travel & Events",
    20: "Gaming",
    21: "Videoblogging",
    22: "People & Blogs",
    23: "Comedy",
    24: "Entertainment",
    25: "News & Politics",
    26: "Howto & Style",
    27: "Education",
    28: "Science & Technology",
    29: "Nonprofits & Activism",
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _resolve_col(df: pd.DataFrame, canonical: str) -> str | None:
    """Return the first matching raw column name, or None."""
    for variant in COLUMN_MAP[canonical]:
        if variant in df.columns:
            return variant
    return None


def _rename_to_canonical(df: pd.DataFrame) -> pd.DataFrame:
    rename: dict[str, str] = {}
    for canonical, variants in COLUMN_MAP.items():
        for v in variants:
            if v in df.columns and v != canonical:
                rename[v] = canonical
                break
    return df.rename(columns=rename)


def _load_category_json(country: str) -> dict[int, str]:
    """Try to load a per-country category JSON, fall back to built-in map."""
    for pattern in [
        f"{country}_category_id.json",
        f"{country}_youtube_category_id.json",
        f"category_id_{country}.json",
    ]:
        path = RAW_DIR / pattern
        if path.exists():
            with open(path) as f:
                raw = json.load(f)
            # Kaggle format: {"kind": "...", "items": [{"id": "1", "snippet": {"title": "..."}}]}
            if "items" in raw:
                return {int(item["id"]): item["snippet"]["title"] for item in raw["items"]}
    return _BUILTIN_CATEGORIES


def _find_csv(country: str) -> Path | None:
    """Locate the raw CSV for a given country code."""
    candidates = [
        f"{country}_Trending.csv",                    # BR_Trending.csv style
        f"{country}_youtube_trending_data.csv",
        f"{country}videos.csv",
        f"{country.lower()}_youtube_trending_data.csv",
        f"{country.lower()}videos.csv",
        f"youtube_{country}_trending.csv",
        f"trending_{country}.csv",
    ]
    for name in candidates:
        p = RAW_DIR / name
        if p.exists():
            return p
    # Fallback: any CSV that starts with the country code
    for p in RAW_DIR.glob(f"{country}*.csv"):
        return p
    for p in RAW_DIR.glob(f"{country.lower()}*.csv"):
        return p
    return None


def _clean_numeric(df: pd.DataFrame, col: str) -> pd.Series:
    s = pd.to_numeric(df[col], errors="coerce")
    s = s.clip(lower=0)
    return s


def _parse_dates(series: pd.Series) -> pd.Series:
    """Parse dates tolerantly; return UTC-normalised datetime64."""
    try:
        parsed = pd.to_datetime(series, utc=True, errors="coerce")
    except Exception:
        parsed = pd.to_datetime(series, errors="coerce", infer_datetime_format=True)
        if parsed.dt.tz is None:
            parsed = parsed.dt.tz_localize("UTC")
        else:
            parsed = parsed.dt.tz_convert("UTC")
    return parsed


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    frames: list[pd.DataFrame] = []

    for country in COUNTRIES:
        csv_path = _find_csv(country)
        if csv_path is None:
            print(f"  [SKIP] {country} — no CSV found in {RAW_DIR}")
            continue

        print(f"  [LOAD] {country} ← {csv_path.name}")
        try:
            df = pd.read_csv(csv_path, encoding="utf-8", low_memory=False)
        except UnicodeDecodeError:
            df = pd.read_csv(csv_path, encoding="latin-1", low_memory=False)

        df = _rename_to_canonical(df)

        # Inject country column
        df["country"] = country

        # Load category map for this country
        cat_map = _load_category_json(country)

        # Ensure required columns exist (fill with NaN if absent)
        for canonical in COLUMN_MAP:
            if canonical not in df.columns:
                print(f"    [WARN] column '{canonical}' not found in {csv_path.name} — filling NaN")
                df[canonical] = np.nan

        # Numeric coercion
        df["view_count"]    = _clean_numeric(df, "view_count")
        df["likes"]         = _clean_numeric(df, "likes")
        df["comment_count"] = _clean_numeric(df, "comment_count")
        df["categoryId"]    = pd.to_numeric(df["categoryId"], errors="coerce")

        # Date parsing
        df["publishedAt"]   = _parse_dates(df["publishedAt"])
        df["trending_date"] = _parse_dates(df["trending_date"])

        # Drop rows missing the two most critical fields
        before = len(df)
        df = df.dropna(subset=["video_id", "title"])
        if len(df) < before:
            print(f"    [DROP] {before - len(df)} rows missing video_id or title")

        # Map category names
        df["category_name"] = df["categoryId"].map(
            lambda cid: cat_map.get(int(cid), "Unknown") if pd.notna(cid) else "Unknown"
        )

        frames.append(df)

    if not frames:
        raise RuntimeError(
            f"No CSV files were loaded from {RAW_DIR}.\n"
            "Check that your raw files are placed in data/raw/ and that COUNTRIES "
            "matches the country codes in your filenames."
        )

    combined = pd.concat(frames, ignore_index=True)
    print(f"\n  Loaded {len(combined):,} rows across {len(frames)} countries")

    # ── Deduplication: keep the row with the highest view_count per video_id + country
    combined = (
        combined
        .sort_values("view_count", ascending=False)
        .drop_duplicates(subset=["video_id", "country"])
        .reset_index(drop=True)
    )
    print(f"  After dedup:  {len(combined):,} rows")

    # ── Drop rows where title is empty / whitespace
    combined = combined[combined["title"].str.strip().str.len() > 0].reset_index(drop=True)

    # ── Select and order final columns
    final_cols = [
        "video_id", "title", "channelTitle", "publishedAt", "trending_date",
        "categoryId", "category_name", "view_count", "likes", "comment_count",
        "country",
    ]
    # Keep any extra columns from the raw files too
    extra = [c for c in combined.columns if c not in final_cols]
    combined = combined[final_cols + extra]

    combined.to_csv(OUT_FILE, index=False)
    print(f"\n  Saved → {OUT_FILE}")
    print(f"  Shape: {combined.shape[0]:,} rows × {combined.shape[1]} columns")
    print(f"  Countries: {sorted(combined['country'].unique().tolist())}")
    print(f"  Categories: {sorted(combined['category_name'].unique().tolist())[:10]} ...")


if __name__ == "__main__":
    main()


