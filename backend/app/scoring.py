"""
scoring.py
==========
Reusable scoring functions consumed by the TrendLift FastAPI app.

All JSON artifacts are loaded lazily on first call and cached for the
lifetime of the process.  No I/O happens at import time.

Importable with no side effects:
    from backend.app.scoring import (
        get_opportunity_score,
        get_breakout_niches,
        get_title_patterns,
        classify_query_cluster,
    )
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_PROJECT_ROOT    = Path(__file__).resolve().parents[2]
_MODELS_DIR      = _PROJECT_ROOT / "backend" / "models"

_OPPORTUNITY_JSON = _MODELS_DIR / "opportunity_scores.json"
_BREAKOUT_JSON    = _MODELS_DIR / "breakout_table.json"
_PATTERNS_JSON    = _MODELS_DIR / "title_patterns.json"

# ---------------------------------------------------------------------------
# Module-level caches (None = not yet loaded)
# ---------------------------------------------------------------------------

# dict[cluster_id -> opportunity_score_dict]
_opportunity_index: dict[int, dict] | None = None

# list already sorted by breakout_score descending
_breakout_table: list[dict] | None = None

# dict[cluster_id -> title_pattern_dict]
_patterns_index: dict[int, dict] | None = None


# ---------------------------------------------------------------------------
# Internal loaders
# ---------------------------------------------------------------------------

def _load_opportunity() -> None:
    global _opportunity_index
    if _opportunity_index is not None:
        return
    with open(_OPPORTUNITY_JSON, encoding="utf-8") as fh:
        records: list[dict] = json.load(fh)
    _opportunity_index = {int(r["cluster_id"]): r for r in records}


def _load_breakout() -> None:
    global _breakout_table
    if _breakout_table is not None:
        return
    with open(_BREAKOUT_JSON, encoding="utf-8") as fh:
        _breakout_table = json.load(fh)   # already sorted desc by build_scores.py


def _load_patterns() -> None:
    global _patterns_index
    if _patterns_index is not None:
        return
    with open(_PATTERNS_JSON, encoding="utf-8") as fh:
        records: list[dict] = json.load(fh)
    _patterns_index = {int(r["cluster_id"]): r for r in records}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_opportunity_score(cluster_id: int) -> dict | None:
    """
    Return the opportunity-score dict for *cluster_id*, or None if not found.

    Keys: cluster_id, opportunity_score, saturation, spread_score,
          engagement_score, cross_country_score, speed_score,
          unique_channels, avg_engagement_score, avg_country_count,
          avg_trend_delay_days
    """
    _load_opportunity()
    return _opportunity_index.get(int(cluster_id))  # type: ignore[union-attr]


def get_breakout_niches(
    category: str | None = None,
    min_score: int = 0,
) -> list[dict]:
    """
    Return clusters sorted by breakout_score descending, capped at 20.

    Parameters
    ----------
    category:  If provided, filter to rows whose dominant_category matches
               (case-insensitive). Pass None to include all categories.
    min_score: Only return clusters with breakout_score >= this value (0–100).
    """
    _load_breakout()
    results: list[dict] = _breakout_table  # type: ignore[assignment]

    if category is not None:
        cat_lower = category.strip().lower()
        results = [
            r for r in results
            if r.get("dominant_category", "").lower() == cat_lower
        ]

    if min_score > 0:
        results = [r for r in results if r.get("breakout_score", 0) >= min_score]

    return results[:20]


def get_title_patterns(cluster_id: int) -> dict | None:
    """
    Return the title-pattern dict for *cluster_id*, or None if not found.

    Keys: cluster_id, median_word_count, median_char_count, median_caps_ratio,
          question_rate, exclamation_rate, colon_rate, number_rate,
          top_first_words, example_titles
    """
    _load_patterns()
    return _patterns_index.get(int(cluster_id))  # type: ignore[union-attr]


def classify_query_cluster(similar_videos: list[dict]) -> int:
    """
    Infer the most relevant topic cluster from a list of similar videos
    (as returned by search_similar()).

    Uses rank-weighted voting: the top result gets weight 1.0, the second
    gets 0.5, the third 0.33, etc.  This prevents large catch-all clusters
    from winning simply because they contain more rows — the highest-similarity
    matches dominate the decision.

    Returns -1 if *similar_videos* is empty or contains no valid cluster ids.
    """
    if not similar_videos:
        return -1

    valid = [
        v for v in similar_videos
        if v.get("topic_cluster") is not None and v["topic_cluster"] != -1
    ]
    if not valid:
        return -1

    # Rank-weighted voting: position 1 gets weight 1.0, position 2 gets 0.5, …
    cluster_weights: dict[int, float] = {}
    for i, v in enumerate(valid):
        weight = 1.0 / (i + 1)
        cid = int(v["topic_cluster"])
        cluster_weights[cid] = cluster_weights.get(cid, 0.0) + weight

    return max(cluster_weights, key=cluster_weights.get)  # type: ignore[arg-type]
