"""
backend/app/main.py
===================
TrendLift FastAPI backend.

Run from the project root:
    uvicorn backend.app.main:app --reload --port 8000

Note: Python treats backend/ and backend/app/ as namespace packages
(PEP 420, Python 3.3+), so no __init__.py files are needed when the
project root is on sys.path (which uvicorn guarantees when invoked from there).
"""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.app.scoring import (
    classify_query_cluster,
    get_breakout_niches,
    get_opportunity_score,
    get_title_patterns,
)
from backend.app.search import search_similar

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_MODELS_DIR   = _PROJECT_ROOT / "backend" / "models"

# ---------------------------------------------------------------------------
# Module-level state populated at startup
# ---------------------------------------------------------------------------
# cluster_id -> top 5 TF-IDF terms (sourced from cluster_profiles.json)
_cluster_terms: dict[int, list[str]] = {}

# Sorted unique dominant_category values from breakout_table.json
_all_categories: list[str] = []


# ---------------------------------------------------------------------------
# Startup warm-up
# ---------------------------------------------------------------------------

def _warm_up() -> None:
    """
    Load all heavy artifacts into memory before any request arrives.
    Called once synchronously inside the lifespan context manager.
    """
    global _cluster_terms, _all_categories

    # Build cluster_id → top_terms index
    with open(_MODELS_DIR / "cluster_profiles.json", encoding="utf-8") as fh:
        profiles: list[dict] = json.load(fh)
    _cluster_terms = {
        int(p["cluster_id"]): p.get("top_terms", []) for p in profiles
    }

    # Build sorted categories list (needs the full breakout table, not the
    # 20-result slice that get_breakout_niches returns)
    with open(_MODELS_DIR / "breakout_table.json", encoding="utf-8") as fh:
        breakout_data: list[dict] = json.load(fh)
    _all_categories = sorted(
        {r["dominant_category"] for r in breakout_data if r.get("dominant_category")}
    )

    # Trigger lazy loading in scoring.py (loads all three JSON caches)
    get_opportunity_score(0)
    get_breakout_niches()
    get_title_patterns(0)

    # Trigger lazy loading in search.py (loads vectorizer + TF-IDF matrix)
    search_similar("test", top_k=1)

    print("TrendLift API ready")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _warm_up()
    yield   # serve requests
    # nothing to tear down


# ---------------------------------------------------------------------------
# App + CORS
# ---------------------------------------------------------------------------

app = FastAPI(title="TrendLift API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _safe_float(value, decimals: int = 4) -> float:
    try:
        return round(float(value), decimals)
    except (TypeError, ValueError):
        return 0.0


def _safe_int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _trend_interpretation(avg_days: float) -> str:
    """Human-readable timing sentence for the validate response."""
    days = max(1, round(avg_days))
    unit = "day" if days == 1 else "days"
    return f"typically trends within {days} {unit}"


# ---------------------------------------------------------------------------
# Endpoint 1 — Health check
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"status": "ok", "message": "TrendLift API is running"}


# ---------------------------------------------------------------------------
# Endpoint 2 — Idea Validator
# ---------------------------------------------------------------------------

@app.get("/api/validate")
def validate(
    query: str = Query(..., description="Topic or video idea to validate"),
    country: str = Query("all", description="ISO country code to filter displayed results (e.g. US, GB). Pass 'all' for no filter."),
):
    """
    Validate a content idea against trending patterns.

    1. Find the 12 most similar trending videos.
    2. Classify them into a topic cluster.
    3. Return opportunity score, title patterns, and similar examples.
    """
    try:
        # 1. Similarity search (full results used for scoring)
        results = search_similar(query, top_k=12)
        if not results:
            return {"error": "No similar content found", "opportunity_score": 0}

        # 2. Classify cluster from similarity results
        cluster_id = classify_query_cluster(results)

        if cluster_id == -1:
            return {
                "query":             query,
                "cluster_id":        -1,
                "error":             "No closely matching content found for this query. Try a broader topic.",
                "opportunity_score": None,
                "saturation":        None,
                "score_components":  None,
                "timing":            None,
                "similar_videos":    [],
                "title_patterns":    None,
                "cluster_top_terms": [],
            }

        # 3. Fetch per-cluster data
        opp      = get_opportunity_score(cluster_id) or {}
        patterns = get_title_patterns(cluster_id) or {}

        # 4. Optionally filter display videos by country (scoring always uses full set)
        display_videos = results
        if country.strip().lower() != "all":
            country_upper = country.strip().upper()
            filtered = [v for v in results if v.get("country", "").upper() == country_upper]
            if filtered:
                display_videos = filtered

        similar_videos = [
            {
                "title":            v.get("title", ""),
                "channel_title":    v.get("channel_title", ""),
                "category_name":    v.get("category_name", ""),
                "country":          v.get("country", ""),
                "views":            _safe_int(v.get("views")),
                "likes_ratio":      _safe_float(v.get("likes_ratio"), 4),
                "trend_delay_days": _safe_float(v.get("trend_delay_days"), 2),
                "channel_tier":     v.get("channel_tier", ""),
            }
            for v in display_videos[:8]
        ]

        avg_delay = _safe_float(opp.get("avg_trend_delay_days", 0.0), 2)

        return {
            "query":             query,
            "cluster_id":        cluster_id,
            "opportunity_score": _safe_int(opp.get("opportunity_score", 0)),
            "saturation":        opp.get("saturation", "Unknown"),
            "score_components": {
                "channel_spread":    _safe_float(opp.get("spread_score", 0.0), 2),
                "engagement_quality": _safe_float(opp.get("engagement_score", 0.0), 2),
                "cross_country":     _safe_float(opp.get("cross_country_score", 0.0), 2),
                "trend_speed":       _safe_float(opp.get("speed_score", 0.0), 2),
            },
            "timing": {
                "avg_trend_delay_days": avg_delay,
                "interpretation":       _trend_interpretation(avg_delay),
            },
            "similar_videos":    similar_videos,
            "title_patterns": {
                "median_word_count": patterns.get("median_word_count", 0.0),
                "question_rate":     patterns.get("question_rate", 0.0),
                "colon_rate":        patterns.get("colon_rate", 0.0),
                "number_rate":       patterns.get("number_rate", 0.0),
                "top_first_words":   patterns.get("top_first_words", {}),
                "example_titles":    patterns.get("example_titles", []),
            },
            "cluster_top_terms": _cluster_terms.get(cluster_id, []),
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Endpoint 3 — Breakout Finder
# ---------------------------------------------------------------------------

@app.get("/api/breakout")
def breakout(
    category: Optional[str] = Query(None, description="Filter by dominant_category (case-insensitive)"),
    min_score: int           = Query(0, ge=0, le=100, description="Minimum breakout_score (0–100)"),
    limit: int               = Query(15, ge=1, le=40, description="Maximum number of results"),
):
    """
    Return the highest-scoring breakout niches, optionally filtered by
    category and minimum score.

    Note: get_breakout_niches() internally caps at 20; the `limit` param
    applies an additional slice on top of that.
    """
    try:
        niches = get_breakout_niches(category=category, min_score=min_score)
        niches = niches[:limit]

        return {
            "niches": [
                {
                    "cluster_id":        n["cluster_id"],
                    "top_terms":         n.get("top_terms", []),
                    "dominant_category": n.get("dominant_category", ""),
                    "breakout_score":    n.get("breakout_score", 0),
                    "gini_score":        n.get("gini_score", 0.0),
                    "breakout_rate":     n.get("breakout_rate", 0.0),
                    "country_arbitrage": n.get("country_arbitrage", False),
                    "unique_channels":   n.get("unique_channels", 0),
                    "opportunity_score": n.get("opportunity_score", 0),
                    "saturation":        n.get("saturation", "Unknown"),
                }
                for n in niches
            ],
            "total": len(niches),
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Endpoint 4 — Title Pattern Analyzer
# ---------------------------------------------------------------------------

@app.get("/api/title-patterns")
def title_patterns(
    query: str = Query(..., description="Topic or video idea to analyze"),
):
    """
    Return detailed title pattern statistics for the topic cluster most
    similar to the given query.
    """
    try:
        results    = search_similar(query, top_k=10)
        cluster_id = classify_query_cluster(results)

        if cluster_id == -1:
            return {
                "query":             query,
                "cluster_id":        -1,
                "error":             "No matching content found. Try a broader or different topic keyword.",
                "patterns":          None,
                "cluster_top_terms": [],
            }

        patterns   = get_title_patterns(cluster_id) or {}

        return {
            "query":      query,
            "cluster_id": cluster_id,
            "patterns": {
                "median_word_count":  patterns.get("median_word_count", 0.0),
                "median_char_count":  patterns.get("median_char_count", 0.0),
                "median_caps_ratio":  patterns.get("median_caps_ratio", 0.0),
                "question_rate":      patterns.get("question_rate", 0.0),
                "exclamation_rate":   patterns.get("exclamation_rate", 0.0),
                "colon_rate":         patterns.get("colon_rate", 0.0),
                "number_rate":        patterns.get("number_rate", 0.0),
                "top_first_words":    patterns.get("top_first_words", {}),
                "example_titles":     patterns.get("example_titles", []),
            },
            "cluster_top_terms": _cluster_terms.get(cluster_id, []),
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Endpoint 5 — Category List
# ---------------------------------------------------------------------------

@app.get("/api/categories")
async def get_categories():
    """
    Return the full sorted list of YouTube categories from the static
    category map — not limited to whichever categories happen to appear
    in the current breakout table.
    """
    try:
        from backend.app.category_map import CATEGORY_MAP
        return {"categories": sorted(set(CATEGORY_MAP.values()))}
    except Exception as exc:
        return {"error": str(exc)}
