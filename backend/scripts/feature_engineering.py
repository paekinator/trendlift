"""
feature_engineering.py
======================
Reads the cleaned TrendLift dataset, computes all engineered features,
and writes the result + a JSON summary report.

Usage (from project root):
    python backend/scripts/feature_engineering.py

Importable API:
    from backend.scripts.feature_engineering import run_feature_engineering
    df, report = run_feature_engineering()
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths (resolved relative to the project root, not this file's directory)
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_CSV = _PROJECT_ROOT / "data" / "processed" / "trending_2026_11c_clean_with_categories.csv"
OUTPUT_CSV = _PROJECT_ROOT / "data" / "processed" / "trending_2026_11c_engineered.csv"
REPORT_JSON = _PROJECT_ROOT / "data" / "processed" / "feature_engineering_report.json"

# ---------------------------------------------------------------------------
# English-country codes used for is_english_country
# ---------------------------------------------------------------------------
ENGLISH_COUNTRIES = {"US", "CA", "GB", "IN"}


# ---------------------------------------------------------------------------
# Helper: clean a single tags string
# ---------------------------------------------------------------------------
def _clean_tags(raw) -> str:
    """Return a space-joined, quote-stripped tag string (or '' for none/NaN)."""
    if pd.isna(raw):
        return ""
    s = str(raw).strip()
    if s.lower() in {"[none]", "none", ""}:
        return ""
    # Strip surrounding/embedded double-quotes, split on '|', rejoin with space
    s = s.replace('"', "")
    parts = [t.strip() for t in s.split("|") if t.strip()]
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Helper: make a Series UTC-aware without shifting values that are already UTC
# ---------------------------------------------------------------------------
def _ensure_utc(series: pd.Series) -> pd.Series:
    """Convert a datetime Series to UTC-aware. Localizes if naive."""
    if series.dt.tz is None:
        return series.dt.tz_localize("UTC")
    return series.dt.tz_convert("UTC")


# ---------------------------------------------------------------------------
# Main engineering function
# ---------------------------------------------------------------------------
def run_feature_engineering(
    input_path: str | Path = INPUT_CSV,
    output_path: str | Path = OUTPUT_CSV,
    report_path: str | Path = REPORT_JSON,
) -> tuple[pd.DataFrame, dict]:
    """
    Load the cleaned CSV, engineer all features, save outputs, return (df, report).
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    report_path = Path(report_path)

    print(f"[feature_engineering] Reading {input_path}")
    df = pd.read_csv(input_path, low_memory=False)
    print(f"[feature_engineering] Loaded {len(df):,} rows, {df.shape[1]} columns")

    # ------------------------------------------------------------------
    # 1. ENGAGEMENT FEATURES
    # ------------------------------------------------------------------
    views = pd.to_numeric(df["view_count"], errors="coerce").fillna(0)
    likes = pd.to_numeric(df["likes"], errors="coerce").fillna(0)
    comments = pd.to_numeric(df["comment_count"], errors="coerce").fillna(0)

    df["likes_ratio"] = (likes / views).where(views != 0, other=0.0).fillna(0.0)
    df["comments_ratio"] = (comments / views).where(views != 0, other=0.0).fillna(0.0)
    df["engagement_score"] = (0.6 * df["likes_ratio"]) + (0.4 * df["comments_ratio"])

    # ------------------------------------------------------------------
    # 2. TREND DELAY
    # ------------------------------------------------------------------
    df["trending_date"] = pd.to_datetime(df["trending_date"], utc=True, errors="coerce")
    df["publishedAt"]   = pd.to_datetime(df["publishedAt"],   utc=True, errors="coerce")

    raw_delay = (df["trending_date"] - df["publishedAt"]).dt.total_seconds() / 86400
    df["trend_delay_days"] = raw_delay.clip(lower=0, upper=60).fillna(0).round(2)

    # ------------------------------------------------------------------
    # 3. CROSS-COUNTRY SPREAD
    # ------------------------------------------------------------------
    country_count = (
        df.groupby("video_id")["country"]
        .nunique()
        .reset_index(name="country_count")
    )
    df = df.merge(country_count, on="video_id", how="left")

    # ------------------------------------------------------------------
    # 4. CHANNEL FOOTPRINT
    # ------------------------------------------------------------------
    channel_video_count = (
        df.groupby("channelTitle")["video_id"]
        .nunique()
        .reset_index(name="channel_video_count")
    )
    channel_country_count = (
        df.groupby("channelTitle")["country"]
        .nunique()
        .reset_index(name="channel_country_count")
    )
    df = df.merge(channel_video_count, on="channelTitle", how="left")
    df = df.merge(channel_country_count, on="channelTitle", how="left")

    # ------------------------------------------------------------------
    # 5. CHANNEL TIER
    # ------------------------------------------------------------------
    df["channel_tier"] = pd.cut(
        df["channel_video_count"],
        bins=[0, 2, 6, 20, float("inf")],
        labels=["breakout", "emerging", "established", "dominant"],
        right=True,
    ).astype(str)  # convert Categorical to plain str to avoid NaN category issues

    # ------------------------------------------------------------------
    # 6. TAGS CLEANING + CONTENT FIELD
    # ------------------------------------------------------------------
    df["tags_clean"] = df["tags"].apply(_clean_tags)
    df["content"] = df["title"].fillna("") + " " + df["tags_clean"]

    # ------------------------------------------------------------------
    # 7. TITLE PATTERN FEATURES
    # ------------------------------------------------------------------
    title = df["title"].fillna("")

    df["title_word_count"] = title.str.split().str.len().fillna(0).astype(int)
    df["title_char_count"] = title.str.len().fillna(0).astype(int)

    # caps_ratio: uppercase letters / total chars (0 for empty titles)
    def _caps_ratio(s: str) -> float:
        if not s:
            return 0.0
        upper_count = sum(1 for c in s if c.isupper())
        return upper_count / len(s)

    df["caps_ratio"] = title.apply(_caps_ratio)

    df["has_question"] = title.str.contains(r"\?", regex=True).astype(int)
    df["has_exclamation"] = title.str.contains(r"!", regex=False).astype(int)
    df["has_colon"] = title.str.contains(r":", regex=False).astype(int)
    df["has_number"] = title.str.contains(r"\d", regex=True).astype(int)

    def _first_word(s: str) -> str:
        words = s.strip().split()
        return words[0].lower() if words else ""

    df["title_first_word"] = title.apply(_first_word)

    # ------------------------------------------------------------------
    # 8. ENGLISH FLAG
    # ------------------------------------------------------------------
    df["is_english_country"] = df["country"].isin(ENGLISH_COUNTRIES).astype(int)

    # ------------------------------------------------------------------
    # SAVE ENGINEERED CSV
    # ------------------------------------------------------------------
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"[feature_engineering] Saved engineered CSV → {output_path}  ({len(df):,} rows)")

    # ------------------------------------------------------------------
    # BUILD + SAVE REPORT
    # ------------------------------------------------------------------
    tier_dist = df["channel_tier"].value_counts().to_dict()

    report: dict = {
        "total_rows": int(len(df)),
        "unique_videos": int(df["video_id"].nunique()),
        "unique_channels": int(df["channelTitle"].nunique()),
        "english_country_rows": int(df["is_english_country"].sum()),
        "avg_likes_ratio": round(float(df["likes_ratio"].mean()), 2),
        "avg_comments_ratio": round(float(df["comments_ratio"].mean()), 2),
        "avg_trend_delay_days": round(float(df["trend_delay_days"].mean()), 2),
        "avg_country_count": round(float(df["country_count"].mean()), 2),
        "channel_tier_distribution": {k: int(v) for k, v in tier_dist.items()},
        "rows_with_zero_trend_delay": int((df["trend_delay_days"] == 0).sum()),
        "rows_with_positive_trend_delay": int((df["trend_delay_days"] > 0).sum()),
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print(f"[feature_engineering] Saved report        → {report_path}")

    return df, report


# ---------------------------------------------------------------------------
# Validation block
# ---------------------------------------------------------------------------
def validate(df: pd.DataFrame, report: dict) -> None:
    """Run assertions and print a summary. Raises AssertionError on failure."""
    print("\n[validation] Running checks…")

    # 1. trend_delay_days: no NaN
    nan_delay = df["trend_delay_days"].isna().sum()
    if nan_delay > 0:
        print(f"  [WARN] trend_delay_days has {nan_delay} NaN rows — date columns may be missing or unparseable. Defaulting to 0.")
    else:
        print(f"  ✓ trend_delay_days  – no NaN ({len(df):,} rows)")

    # 2. likes_ratio: no NaN
    nan_lr = df["likes_ratio"].isna().sum()
    assert nan_lr == 0, f"likes_ratio has {nan_lr} NaN value(s)"
    print(f"  ✓ likes_ratio       – no NaN")

    # 3. channel_tier: no NaN / 'nan' strings
    bad_tier = df["channel_tier"].isin(["nan", "NaN", "None", "none"]).sum()
    assert bad_tier == 0, f"channel_tier has {bad_tier} NaN-like value(s)"
    print(f"  ✓ channel_tier      – no NaN")

    # 4. country_count between 1 and 11
    out_of_range = ((df["country_count"] < 1) | (df["country_count"] > 11)).sum()
    assert out_of_range == 0, f"country_count has {out_of_range} row(s) outside [1, 11]"
    print(f"  ✓ country_count     – all in [1, 11]")

    # 5. is_english_country only 0 or 1
    bad_flag = (~df["is_english_country"].isin([0, 1])).sum()
    assert bad_flag == 0, f"is_english_country has {bad_flag} non-binary value(s)"
    print(f"  ✓ is_english_country – only 0/1")

    # Print key stats
    print("\n[validation] Summary stats:")
    print(f"  total_rows              : {report['total_rows']:,}")
    print(f"  unique_videos           : {report['unique_videos']:,}")
    print(f"  unique_channels         : {report['unique_channels']:,}")
    print(f"  english_country_rows    : {report['english_country_rows']:,}")
    print(f"  avg_likes_ratio         : {report['avg_likes_ratio']}")
    print(f"  avg_comments_ratio      : {report['avg_comments_ratio']}")
    print(f"  avg_trend_delay_days    : {report['avg_trend_delay_days']}")
    print(f"  avg_country_count       : {report['avg_country_count']}")
    print(f"  rows_with_zero_delay    : {report['rows_with_zero_trend_delay']:,}")
    print(f"  rows_with_positive_delay: {report['rows_with_positive_trend_delay']:,}")
    print(f"  channel_tier_distribution:")
    for tier, cnt in report["channel_tier_distribution"].items():
        print(f"      {tier:<12}: {cnt:,}")

    print("\n[validation] All checks passed.\n")


# ---------------------------------------------------------------------------
# __main__ entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    df, report = run_feature_engineering()
    validate(df, report)


