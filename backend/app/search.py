"""
search.py
=========
Reusable similarity search over the TF-IDF indexed English trending corpus.
Artifacts are loaded lazily on the first call to search_similar().

Importable with no side effects:
    from backend.app.search import search_similar

    results = search_similar("cooking challenge reaction", top_k=10)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity as _cosine_sim

# ---------------------------------------------------------------------------
# Paths (anchored to project root, wherever this file lives)
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_MODELS_DIR   = _PROJECT_ROOT / "backend" / "models"
_CLUSTERED_CSV = _PROJECT_ROOT / "data" / "processed" / "trending_english_clustered.csv"

# ---------------------------------------------------------------------------
# Module-level artifact cache (None until first call)
# ---------------------------------------------------------------------------
_vectorizer:   Any | None = None   # TfidfVectorizer
_tfidf_matrix: Any | None = None   # scipy sparse (n_rows × n_features)
_video_ids:    Any | None = None   # np.ndarray shape (n_rows,): row i → video_id
_df:           pd.DataFrame | None = None  # clustered CSV, positional index = matrix row


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_artifacts() -> None:
    """Load all artifacts into module-level cache. No-op after first call."""
    global _vectorizer, _tfidf_matrix, _video_ids, _df

    if _vectorizer is not None:
        return  # already loaded

    _vectorizer   = joblib.load(_MODELS_DIR / "tfidf_vectorizer.pkl")
    _tfidf_matrix = joblib.load(_MODELS_DIR / "tfidf_matrix.pkl")
    _video_ids    = joblib.load(_MODELS_DIR / "english_video_ids.pkl")

    # The clustered CSV has the same row order as the matrix (guaranteed by
    # build_clusters.py which resets the index before saving both).
    _df = pd.read_csv(_CLUSTERED_CSV, low_memory=False)


def _safe_str(val: Any, default: str = "") -> str:
    return str(val) if pd.notna(val) else default


def _safe_int(val: Any, default: int = 0) -> int:
    try:
        return int(float(val)) if pd.notna(val) else default
    except (ValueError, TypeError):
        return default


def _safe_float(val: Any, default: float = 0.0) -> float:
    try:
        return float(val) if pd.notna(val) else default
    except (ValueError, TypeError):
        return default


def _row_to_dict(row: pd.Series) -> dict:
    return {
        "video_id":         _safe_str(row.get("video_id")),
        "title":            _safe_str(row.get("title")),
        "channel_title":    _safe_str(row.get("channel_title")),
        "category_name":    _safe_str(row.get("category_name")),
        "country":          _safe_str(row.get("country")),
        "views":            _safe_int(row.get("views")),
        "likes_ratio":      _safe_float(row.get("likes_ratio")),
        "comments_ratio":   _safe_float(row.get("comments_ratio")),
        "trend_delay_days": _safe_float(row.get("trend_delay_days")),
        "country_count":    _safe_int(row.get("country_count")),
        "channel_tier":     _safe_str(row.get("channel_tier")),
        "topic_cluster":    _safe_int(row.get("topic_cluster"), default=-1),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def search_similar(query: str, top_k: int = 10) -> list[dict]:
    """
    Transform *query* with the TF-IDF vectorizer and return the *top_k* most
    similar videos from the English trending corpus, deduplicated by video_id.

    Parameters
    ----------
    query:  Free-text query (title keywords, topic terms, etc.)
    top_k:  Maximum number of unique-video results to return.

    Returns
    -------
    List of dicts ordered by descending cosine similarity.
    Returns an empty list when the query is blank or matches nothing.
    """
    if not query or not query.strip():
        return []

    _load_artifacts()

    # Transform query → sparse row vector
    query_vec = _vectorizer.transform([query.strip()])

    # Cosine similarity against every row in the corpus
    similarities: np.ndarray = _cosine_sim(query_vec, _tfidf_matrix).flatten()

    # Suppress near-zero matches — queries with little vocabulary overlap
    # (e.g. "personal finance") would otherwise return random low-signal rows.
    MIN_SIMILARITY = 0.05
    similarities[similarities < MIN_SIMILARITY] = 0.0

    if float(similarities.max()) == 0.0:
        return []  # all scores below threshold → no usable results

    # Sort all rows descending by similarity; slice to a generous candidate pool
    # so deduplication by video_id still yields top_k results after collisions.
    sorted_indices = np.argsort(similarities)[::-1]

    # Deduplicate: keep the first (highest-scoring) row per video_id.
    # Insertion order of a dict (Python 3.7+) preserves ranking automatically.
    seen: dict[str, int] = {}   # video_id → matrix row index
    for idx in sorted_indices:
        if float(similarities[idx]) == 0.0:
            break   # remaining rows have zero similarity — stop early
        vid = str(_video_ids[idx])
        if vid not in seen:
            seen[vid] = int(idx)
        if len(seen) >= top_k:
            break

    results: list[dict] = []
    for vid, row_idx in seen.items():
        row = _df.iloc[row_idx]
        results.append(_row_to_dict(row))

    return results
