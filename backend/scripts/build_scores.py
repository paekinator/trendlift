"""
build_scores.py
===============
Pre-computes all score tables that power TrendLift's Idea Validator and
Breakout Finder features.

Usage (from project root):
    python backend/scripts/build_scores.py

Outputs
-------
backend/models/opportunity_scores.json   — per-cluster opportunity scores
backend/models/breakout_table.json       — breakout-finder table, sorted desc
backend/models/title_patterns.json       — per-cluster title pattern stats
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODELS_DIR       = _PROJECT_ROOT / "backend" / "models"
ENGINEERED_CSV   = _PROJECT_ROOT / "data" / "processed" / "trending_2026_11c_engineered.csv"
CLUSTERED_CSV    = _PROJECT_ROOT / "data" / "processed" / "trending_english_clustered.csv"
PROFILES_JSON    = MODELS_DIR / "cluster_profiles.json"

OPPORTUNITY_JSON = MODELS_DIR / "opportunity_scores.json"
BREAKOUT_JSON    = MODELS_DIR / "breakout_table.json"
PATTERNS_JSON    = MODELS_DIR / "title_patterns.json"

ENGLISH_COUNTRIES     = {"US", "CA", "GB", "IN"}
NON_ENGLISH_COUNTRIES = {"BR", "DE", "FR", "JP", "KR", "MX", "RU"}


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _gini(values: list) -> float:
    """
    Gini coefficient for an iterable of non-negative numbers.
    Returns 0 for empty or all-zero inputs.
    """
    n = len(values)
    if n == 0:
        return 0.0
    arr = sorted(values)
    total = sum(arr)
    if total == 0:
        return 0.0
    cumsum = 0
    for i, v in enumerate(arr):
        cumsum += (2 * (i + 1) - n - 1) * v
    return cumsum / (n * total)


def _load_inputs() -> tuple[list[dict], pd.DataFrame, pd.DataFrame]:
    """Return (cluster_profiles, full_df, english_df)."""
    print("[load] Reading cluster profiles …")
    with open(PROFILES_JSON, encoding="utf-8") as fh:
        profiles: list[dict] = json.load(fh)
    print(f"       {len(profiles)} cluster profiles loaded")

    print("[load] Reading full engineered CSV …")
    full_df = pd.read_csv(ENGINEERED_CSV, low_memory=False)
    print(f"       {len(full_df):,} rows")

    print("[load] Reading English clustered CSV …")
    english_df = pd.read_csv(CLUSTERED_CSV, low_memory=False)
    print(f"       {len(english_df):,} rows, {english_df['topic_cluster'].nunique()} clusters")

    return profiles, full_df, english_df


# ---------------------------------------------------------------------------
# Part A — Opportunity Score Calibration
# ---------------------------------------------------------------------------

def _build_opportunity_scores(profiles: list[dict]) -> list[dict]:
    """
    Compute per-cluster opportunity scores from cluster_profiles.json.
    Saves opportunity_scores.json and returns the list.
    """
    print("\n[A] Building opportunity scores …")
    results: list[dict] = []

    for p in profiles:
        cid               = int(p["cluster_id"])
        unique_channels   = float(p["unique_channels"])
        avg_engagement    = float(p["avg_engagement_score"])
        avg_country_count = float(p["avg_country_count"])
        avg_delay         = float(p["avg_trend_delay_days"])

        spread_score       = min(unique_channels / 50.0, 1.0)
        engagement_score   = min(avg_engagement / 0.08, 1.0)
        cross_country_score = min(avg_country_count / 5.0, 1.0)
        speed_score        = max(0.0, 1.0 - (avg_delay / 60.0))

        raw_score = (
            0.35 * spread_score
            + 0.25 * engagement_score
            + 0.25 * cross_country_score
            + 0.15 * speed_score
        )
        opportunity_score = int(round(raw_score * 100))

        if unique_channels <= 10:
            saturation = "Crowded"
        elif unique_channels <= 30:
            saturation = "Moderate"
        else:
            saturation = "Under-served"

        results.append({
            "cluster_id":           cid,
            "opportunity_score":    opportunity_score,
            "saturation":           saturation,
            "spread_score":         round(spread_score, 4),
            "engagement_score":     round(engagement_score, 4),
            "cross_country_score":  round(cross_country_score, 4),
            "speed_score":          round(speed_score, 4),
            "unique_channels":      int(unique_channels),
            "avg_engagement_score": round(avg_engagement, 4),
            "avg_country_count":    round(avg_country_count, 2),
            "avg_trend_delay_days": round(avg_delay, 2),
        })

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    with open(OPPORTUNITY_JSON, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    scores_range = f"{min(r['opportunity_score'] for r in results)}–{max(r['opportunity_score'] for r in results)}"
    print(f"    Saved: opportunity_scores.json  ({len(results)} clusters, scores {scores_range})")
    return results


# ---------------------------------------------------------------------------
# Part B — Breakout Finder Table
# ---------------------------------------------------------------------------

def _build_country_arbitrage(
    english_df: pd.DataFrame,
    full_df: pd.DataFrame,
) -> dict[int, bool]:
    """
    Map cluster_id → bool indicating whether videos in the cluster appear in
    both an English-dominant country AND at least one non-English country
    (using the full 11-country dataset merged via video_id).
    """
    # video_id → topic_cluster (first occurrence wins; content is identical
    # for the same video so the cluster is deterministic)
    vid_cluster = (
        english_df[["video_id", "topic_cluster"]]
        .drop_duplicates(subset="video_id")
    )
    full_annotated = full_df.merge(vid_cluster, on="video_id", how="inner")

    # For each cluster, collect the set of countries its videos appeared in
    cluster_countries: dict[int, set] = (
        full_annotated
        .groupby("topic_cluster")["country"]
        .apply(set)
        .to_dict()
    )

    arbitrage: dict[int, bool] = {}
    for cid, countries in cluster_countries.items():
        has_english     = bool(countries & ENGLISH_COUNTRIES)
        has_non_english = bool(countries & NON_ENGLISH_COUNTRIES)
        arbitrage[int(cid)] = has_english and has_non_english

    return arbitrage


def _build_breakout_table(
    profiles: list[dict],
    opportunity_scores: list[dict],
    english_df: pd.DataFrame,
    full_df: pd.DataFrame,
) -> list[dict]:
    """
    Compute the Breakout Finder table and save to breakout_table.json.
    """
    print("\n[B] Building breakout table …")

    # Pre-index opportunity scores for O(1) lookup
    opp_index: dict[int, dict] = {r["cluster_id"]: r for r in opportunity_scores}

    # Pre-compute country arbitrage for all clusters in one pass
    country_arbitrage = _build_country_arbitrage(english_df, full_df)

    # Pre-index cluster profiles by cluster_id
    profiles_index: dict[int, dict] = {int(p["cluster_id"]): p for p in profiles}

    rows: list[dict] = []
    cluster_ids = sorted(english_df["topic_cluster"].dropna().unique().astype(int))

    for cid in cluster_ids:
        cid = int(cid)  # np.int64 → Python int so json.dump can serialize it
        cdf = english_df[english_df["topic_cluster"] == cid]
        if len(cdf) == 0:
            continue

        # --- Step 1: Gini coefficient ---
        # One value per unique channel (channel_video_count is a per-channel metric)
        channel_counts = (
            cdf.drop_duplicates(subset="channelTitle")["channel_video_count"]
            .dropna()
            .tolist()
        )
        gini_score  = _gini(channel_counts)
        inverse_gini = round(1.0 - gini_score, 4)
        gini_score   = round(gini_score, 4)

        # --- Step 2: Breakout rate (recomputed from raw data) ---
        breakout_rate = float((cdf["channel_tier"] == "breakout").mean())

        # --- Step 3: Breakout engagement quality ---
        breakout_rows = cdf[cdf["channel_tier"] == "breakout"]
        if len(breakout_rows) > 0:
            breakout_engagement = float(breakout_rows["engagement_score"].mean())
        else:
            breakout_engagement = 0.0

        # --- Step 4: Country arbitrage ---
        arbitrage = country_arbitrage.get(cid, False)

        # --- Step 5: Breakout score ---
        unique_ch = int(cdf["channelTitle"].nunique())

        if unique_ch == 1:
            # Hard gate: a single-channel cluster is a monopoly, not an
            # opportunity. Gini of a length-1 array is 0 → inverse_gini = 1,
            # which would incorrectly boost the score. Force it to the floor.
            breakout_score = 5
        else:
            raw_breakout = (
                0.40 * inverse_gini
                + 0.25 * breakout_rate
                + 0.20 * min(breakout_engagement / 0.08, 1.0)
                + 0.15 * (1.0 if arbitrage else 0.5)
            )
            if unique_ch < 5:
                # Thin-field penalty: subtract 40 points for near-monopoly clusters
                breakout_score = max(0, int(round(raw_breakout * 100)) - 40)
            else:
                breakout_score = int(round(raw_breakout * 100))

        # Pull descriptive fields from profiles
        p   = profiles_index.get(cid, {})
        opp = opp_index.get(cid, {})

        rows.append({
            "cluster_id":          cid,
            "top_terms":           p.get("top_terms", []),
            "dominant_category":   p.get("dominant_category", "Unknown"),
            "breakout_score":      breakout_score,
            "gini_score":          gini_score,
            "inverse_gini":        inverse_gini,
            "breakout_rate":       round(breakout_rate, 4),
            "breakout_engagement": round(breakout_engagement, 4),
            "country_arbitrage":   bool(arbitrage),
            "unique_channels":     unique_ch,
            "total_videos":        int(cdf["video_id"].nunique()),
            "opportunity_score":   opp.get("opportunity_score", 0),
            "saturation":          opp.get("saturation", "Unknown"),
        })

    # Sort by breakout_score descending
    rows.sort(key=lambda r: r["breakout_score"], reverse=True)

    with open(BREAKOUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(rows, fh, indent=2)
    score_range = f"{rows[-1]['breakout_score']}–{rows[0]['breakout_score']}" if rows else "n/a"
    print(f"    Saved: breakout_table.json  ({len(rows)} clusters, scores {score_range})")
    return rows


# ---------------------------------------------------------------------------
# Part C — Title Pattern Table
# ---------------------------------------------------------------------------

def _build_title_patterns(english_df: pd.DataFrame) -> list[dict]:
    """
    Compute per-cluster title pattern statistics and save title_patterns.json.
    """
    print("\n[C] Building title patterns …")
    patterns: list[dict] = []

    cluster_ids = sorted(english_df["topic_cluster"].dropna().unique().astype(int))

    for cid in cluster_ids:
        cid = int(cid)  # np.int64 → Python int so json.dump can serialize it
        cdf = english_df[english_df["topic_cluster"] == cid].copy()
        if len(cdf) == 0:
            continue

        # Median metrics (float, 2 dp)
        median_word_count  = round(float(cdf["title_word_count"].median()), 2)
        median_char_count  = round(float(cdf["title_char_count"].median()), 2)
        median_caps_ratio  = round(float(cdf["caps_ratio"].median()), 4)

        # Binary-column rates (fraction of rows where flag == 1)
        n = len(cdf)
        question_rate    = round(float((cdf["has_question"]    == 1).sum()) / n, 4)
        exclamation_rate = round(float((cdf["has_exclamation"] == 1).sum()) / n, 4)
        colon_rate       = round(float((cdf["has_colon"]       == 1).sum()) / n, 4)
        number_rate      = round(float((cdf["has_number"]      == 1).sum()) / n, 4)

        # Top 5 first words (exclude empty string)
        first_words = cdf["title_first_word"].replace("", np.nan).dropna()
        top_first_words: dict[str, int] = (
            first_words.value_counts().head(5).to_dict()
        )
        top_first_words = {k: int(v) for k, v in top_first_words.items()}

        # 3 reproducible example titles (use random_state for determinism)
        titles_pool = cdf["title"].dropna()
        sample_n    = min(3, len(titles_pool))
        example_titles: list[str] = (
            titles_pool.sample(n=sample_n, random_state=42).tolist()
            if sample_n > 0 else []
        )

        patterns.append({
            "cluster_id":        cid,
            "median_word_count": median_word_count,
            "median_char_count": median_char_count,
            "median_caps_ratio": median_caps_ratio,
            "question_rate":     question_rate,
            "exclamation_rate":  exclamation_rate,
            "colon_rate":        colon_rate,
            "number_rate":       number_rate,
            "top_first_words":   top_first_words,
            "example_titles":    example_titles,
        })

    with open(PATTERNS_JSON, "w", encoding="utf-8") as fh:
        json.dump(patterns, fh, indent=2)
    print(f"    Saved: title_patterns.json  ({len(patterns)} clusters)")
    return patterns


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    profiles, full_df, english_df = _load_inputs()
    opportunity_scores = _build_opportunity_scores(profiles)
    _build_breakout_table(profiles, opportunity_scores, english_df, full_df)
    _build_title_patterns(english_df)
    print(f"\n[build_scores] All score tables saved to {MODELS_DIR}")


if __name__ == "__main__":
    main()


