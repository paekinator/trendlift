"""
build_clusters.py
=================
Trains the TF-IDF vectorizer and KMeans topic clusters on English-country
YouTube trending videos, then writes all model artifacts and summary files.

Usage (from project root):
    python backend/scripts/build_clusters.py

Outputs
-------
backend/models/tfidf_vectorizer.pkl
backend/models/tfidf_matrix.pkl
backend/models/english_video_ids.pkl
backend/models/kmeans_model.pkl
backend/models/cluster_labels.json
backend/models/cluster_profiles.json
data/processed/trending_english_clustered.csv
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_CSV     = _PROJECT_ROOT / "data" / "processed" / "trending_2026_11c_engineered.csv"
CLUSTERED_CSV = _PROJECT_ROOT / "data" / "processed" / "trending_english_clustered.csv"
MODELS_DIR    = _PROJECT_ROOT / "backend" / "models"

N_CLUSTERS = 40


# ---------------------------------------------------------------------------
# Step helpers
# ---------------------------------------------------------------------------

def _load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (full_df, english_df). english_df has a clean 0-based index."""
    print(f"[1] Loading {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV, low_memory=False)
    print(f"    Full dataset: {len(df):,} rows, {df.shape[1]} columns")

    eng = df[df["is_english_country"] == 1].copy()
    eng = eng.dropna(subset=["content"])
    eng = eng[eng["content"].str.strip() != ""].copy()
    eng = eng.reset_index(drop=True)   # critical: 0-based to align with matrix rows
    print(f"    English rows after filtering: {len(eng):,}")
    return df, eng


def _vectorize(english_df: pd.DataFrame) -> tuple[TfidfVectorizer, object]:
    """Fit TF-IDF on english_df['content'], save artifacts, return (vectorizer, matrix)."""
    print("[2] Fitting TF-IDF vectorizer …")
    vectorizer = TfidfVectorizer(
        max_features=8000,
        ngram_range=(1, 2),
        stop_words="english",
        min_df=2,
        sublinear_tf=True,
    )
    matrix = vectorizer.fit_transform(english_df["content"])
    print(f"    Matrix shape: {matrix.shape}  (sparse: {matrix.nnz:,} non-zero entries)")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(vectorizer, MODELS_DIR / "tfidf_vectorizer.pkl")
    joblib.dump(matrix,     MODELS_DIR / "tfidf_matrix.pkl")
    joblib.dump(english_df["video_id"].values, MODELS_DIR / "english_video_ids.pkl")
    print(f"    Saved: tfidf_vectorizer.pkl, tfidf_matrix.pkl, english_video_ids.pkl")
    return vectorizer, matrix


def _cluster(matrix: object, english_df: pd.DataFrame) -> KMeans:
    """Run KMeans, attach labels to english_df, save model."""
    print(f"[3] Running KMeans (n_clusters={N_CLUSTERS}, n_init=10) …")
    km = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
    km.fit(matrix)
    print(f"    Inertia: {km.inertia_:,.2f}")

    joblib.dump(km, MODELS_DIR / "kmeans_model.pkl")
    english_df["topic_cluster"] = km.labels_
    dist = pd.Series(km.labels_).value_counts().sort_index()
    print(f"    Cluster size range: {dist.min()}–{dist.max()} rows per cluster")
    return km


def _label_clusters(
    vectorizer: TfidfVectorizer,
    matrix: object,
    english_df: pd.DataFrame,
) -> dict[int, dict]:
    """
    For each cluster: top-5 mean TF-IDF terms + dominant category_name.
    Returns {cluster_id: {top_terms: [...], dominant_category: str}}.
    """
    print("[4] Labeling clusters …")
    feature_names = vectorizer.get_feature_names_out()
    labels: dict[int, dict] = {}

    for cid in range(N_CLUSTERS):
        mask = (english_df["topic_cluster"] == cid).values
        if mask.sum() == 0:
            labels[cid] = {"top_terms": [], "dominant_category": "Unknown"}
            continue

        cluster_matrix = matrix[mask]
        # mean TF-IDF weight per term across all rows in this cluster
        mean_weights = np.asarray(cluster_matrix.mean(axis=0)).flatten()
        top_idx = mean_weights.argsort()[-5:][::-1]
        top_terms = [feature_names[i] for i in top_idx]

        cat_vals = english_df.loc[mask, "category_name"].dropna()
        dominant_category = (
            str(cat_vals.mode().iloc[0]) if len(cat_vals) > 0 else "Unknown"
        )

        labels[cid] = {"top_terms": top_terms, "dominant_category": dominant_category}

    # JSON keys must be strings
    serializable = {str(k): v for k, v in labels.items()}
    with open(MODELS_DIR / "cluster_labels.json", "w", encoding="utf-8") as fh:
        json.dump(serializable, fh, indent=2)
    print(f"    Saved: cluster_labels.json")
    return labels


def _build_profiles(
    english_df: pd.DataFrame,
    full_df: pd.DataFrame,
    labels: dict[int, dict],
) -> list[dict]:
    """
    Compute per-cluster stats. country_count in english_df was pre-computed
    from the full 11-country dataset during feature engineering, so it already
    represents cross-country spread — no re-merge needed.
    """
    print("[5] Building cluster profiles …")
    profiles: list[dict] = []

    for cid in range(N_CLUSTERS):
        cdf = english_df[english_df["topic_cluster"] == cid]
        if len(cdf) == 0:
            continue

        breakout_channels = int(
            cdf[cdf["channel_tier"] == "breakout"]["channelTitle"].nunique()
        )
        breakout_rate = float((cdf["channel_tier"] == "breakout").mean())

        profile = {
            "cluster_id":            cid,
            "top_terms":             labels[cid]["top_terms"],
            "dominant_category":     labels[cid]["dominant_category"],
            "total_videos":          int(cdf["video_id"].nunique()),
            "unique_channels":       int(cdf["channelTitle"].nunique()),
            "avg_likes_ratio":       round(float(cdf["likes_ratio"].mean()), 4),
            "avg_comments_ratio":    round(float(cdf["comments_ratio"].mean()), 4),
            "avg_engagement_score":  round(float(cdf["engagement_score"].mean()), 4),
            "avg_trend_delay_days":  round(float(cdf["trend_delay_days"].mean()), 2),
            "avg_country_count":     round(float(cdf["country_count"].mean()), 2),
            "breakout_channel_count": breakout_channels,
            "breakout_rate":         round(breakout_rate, 4),
        }
        profiles.append(profile)

    with open(MODELS_DIR / "cluster_profiles.json", "w", encoding="utf-8") as fh:
        json.dump(profiles, fh, indent=2)
    print(f"    Saved: cluster_profiles.json ({len(profiles)} cluster profiles)")
    return profiles


def _save_clustered_csv(english_df: pd.DataFrame) -> None:
    """Save english_df with topic_cluster column."""
    print("[6] Saving clustered CSV …")
    CLUSTERED_CSV.parent.mkdir(parents=True, exist_ok=True)
    english_df.to_csv(CLUSTERED_CSV, index=False)
    print(f"    Saved: {CLUSTERED_CSV}  ({len(english_df):,} rows)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    full_df, english_df = _load_data()
    vectorizer, matrix  = _vectorize(english_df)
    _cluster(matrix, english_df)
    labels   = _label_clusters(vectorizer, matrix, english_df)
    _build_profiles(english_df, full_df, labels)
    _save_clustered_csv(english_df)
    print("\n[build_clusters] All artifacts saved to", MODELS_DIR)


if __name__ == "__main__":
    main()


