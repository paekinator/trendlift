from pathlib import Path
import json
import re
import pandas as pd
import numpy as np

RAW_DIR = Path("~/trendlift/data/raw").expanduser()
PROCESSED_DIR = Path("~/trendlift/data/processed").expanduser()

OUTPUT_CSV = PROCESSED_DIR / "trending_2026_11c_clean.csv"
REPORT_JSON = PROCESSED_DIR / "cleaning_report.json"

EXPECTED_COLUMNS = [
    "video_id",
    "trending_date",
    "title",
    "channel_title",
    "views",
    "likes",
    "dislikes",
    "publish_time",
    "category_id",
    "tags",
    "comments",
    "channel_id",
    "description",
]

COUNTRY_FILE_PATTERN = re.compile(r"^([A-Z]{2})_Trending\.csv$")


def parse_country_from_filename(filename: str) -> str:
    match = COUNTRY_FILE_PATTERN.match(filename)
    if not match:
        raise ValueError(f"Filename does not match expected pattern XX_Trending.csv: {filename}")
    return match.group(1)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip() for c in df.columns]

    # Some datasets use slightly inconsistent naming; normalize here if needed
    rename_map = {
        "comment_count": "comments",
    }
    df = df.rename(columns=rename_map)

    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")

    # Keep only expected columns, in the correct order
    df = df[EXPECTED_COLUMNS].copy()
    return df


def parse_trending_date(value):
    """
    The uploaded files appear to use a non-standard snapshot-like date string,
    commonly looking like 26.26.02 in your samples.
    We handle:
    - YYYY-MM-DD
    - YY.DD.MM
    - DD.MM.YY
    - other parseable strings
    """
    if pd.isna(value):
        return pd.NaT

    s = str(value).strip()

    # Try standard parse first
    dt = pd.to_datetime(s, errors="coerce", utc=True)
    if not pd.isna(dt):
        return dt

    # Try dot-separated custom patterns
    parts = s.split(".")
    if len(parts) == 3 and all(p.isdigit() for p in parts):
        a, b, c = parts

        # Attempt YY.DD.MM
        try:
            year = 2000 + int(a)
            day = int(b)
            month = int(c)
            return pd.Timestamp(year=year, month=month, day=day, tz="UTC")
        except Exception:
            pass

        # Attempt DD.MM.YY
        try:
            day = int(a)
            month = int(b)
            year = 2000 + int(c)
            return pd.Timestamp(year=year, month=month, day=day, tz="UTC")
        except Exception:
            pass

    return pd.NaT


def clean_one_file(path: Path) -> pd.DataFrame:
    country = parse_country_from_filename(path.name)

    df = pd.read_csv(path)
    df = normalize_columns(df)
    df["country"] = country

    # Basic text cleanup
    text_cols = ["video_id", "title", "channel_title", "tags", "channel_id", "description"]
    for col in text_cols:
        df[col] = df[col].fillna("").astype(str).str.strip()

    # Datetime cleanup
    df["publish_time"] = pd.to_datetime(df["publish_time"], errors="coerce", utc=True)
    df["trending_date"] = df["trending_date"].apply(parse_trending_date)

    # Numeric cleanup
    numeric_cols = ["views", "likes", "dislikes", "comments", "category_id"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Fill missing text fields
    df["title"] = df["title"].fillna("")
    df["tags"] = df["tags"].fillna("")
    df["description"] = df["description"].fillna("")
    df["channel_title"] = df["channel_title"].fillna("")
    df["video_id"] = df["video_id"].fillna("")
    df["channel_id"] = df["channel_id"].fillna("")

    # Drop rows missing hard requirements
    df = df[df["video_id"] != ""].copy()
    df = df[df["channel_id"] != ""].copy()
    df = df[~df["publish_time"].isna()].copy()
    df = df[~df["trending_date"].isna()].copy()

    # Fill numeric nulls conservatively
    for col in ["views", "likes", "dislikes", "comments"]:
        df[col] = df[col].fillna(0)

    # Category may be missing in rare cases
    df["category_id"] = df["category_id"].fillna(-1).astype(int)

    # Remove impossible negatives
    for col in ["views", "likes", "dislikes", "comments"]:
        df[col] = df[col].clip(lower=0)

    # Remove exact duplicate rows
    df = df.drop_duplicates()

    return df


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(
        p for p in RAW_DIR.glob("*_Trending.csv")
        if COUNTRY_FILE_PATTERN.match(p.name)
    )

    if len(csv_files) == 0:
        raise FileNotFoundError(f"No country CSV files found in {RAW_DIR}")

    frames = []
    file_reports = []

    for path in csv_files:
        raw_df = pd.read_csv(path)
        raw_rows = len(raw_df)

        cleaned_df = clean_one_file(path)
        clean_rows = len(cleaned_df)

        frames.append(cleaned_df)

        file_reports.append({
            "file": path.name,
            "country": parse_country_from_filename(path.name),
            "raw_rows": raw_rows,
            "clean_rows": clean_rows,
            "dropped_rows": raw_rows - clean_rows,
        })

    merged = pd.concat(frames, ignore_index=True)

    # Remove exact duplicates after merge
    before_merge_dedup = len(merged)
    merged = merged.drop_duplicates()
    after_merge_dedup = len(merged)

    # Create a stable row id for debugging
    merged = merged.reset_index(drop=True)
    merged["row_id"] = np.arange(1, len(merged) + 1)

    # Reorder columns
    final_columns = [
        "row_id",
        "country",
        "video_id",
        "channel_id",
        "channel_title",
        "title",
        "tags",
        "description",
        "category_id",
        "views",
        "likes",
        "dislikes",
        "comments",
        "publish_time",
        "trending_date",
    ]
    merged = merged[final_columns].copy()

    # Save CSV
    merged.to_csv(OUTPUT_CSV, index=False)

    # Build report
    report = {
        "input_folder": str(RAW_DIR),
        "output_csv": str(OUTPUT_CSV),
        "files_processed": len(csv_files),
        "countries": sorted(merged["country"].dropna().unique().tolist()),
        "total_rows_final": int(len(merged)),
        "total_unique_videos": int(merged["video_id"].nunique()),
        "total_unique_channels": int(merged["channel_id"].nunique()),
        "merge_duplicates_removed": int(before_merge_dedup - after_merge_dedup),
        "rows_per_country": merged["country"].value_counts().sort_index().to_dict(),
        "null_counts_final": merged.isna().sum().to_dict(),
        "file_reports": file_reports,
        "date_ranges": {
            "publish_time_min": str(merged["publish_time"].min()),
            "publish_time_max": str(merged["publish_time"].max()),
            "trending_date_min": str(merged["trending_date"].min()),
            "trending_date_max": str(merged["trending_date"].max()),
        },
    }

    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("Done.")
    print(f"Saved cleaned dataset to: {OUTPUT_CSV}")
    print(f"Saved cleaning report to: {REPORT_JSON}")
    print(f"Final rows: {len(merged):,}")
    print(f"Unique videos: {merged['video_id'].nunique():,}")
    print(f"Unique channels: {merged['channel_id'].nunique():,}")


if __name__ == "__main__":
    main()