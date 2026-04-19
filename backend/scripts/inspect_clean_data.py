from pathlib import Path
import pandas as pd

CLEAN_CSV = Path("~/trendlift/data/processed/trending_2026_11c_clean.csv").expanduser()

df = pd.read_csv(CLEAN_CSV)

print("\n=== SHAPE ===")
print(df.shape)

print("\n=== COLUMNS ===")
print(df.columns.tolist())

print("\n=== COUNTRIES ===")
print(sorted(df["country"].unique().tolist()))

print("\n=== ROWS PER COUNTRY ===")
print(df["country"].value_counts().sort_index())

print("\n=== CATEGORY IDS ===")
print(sorted(df["category_id"].dropna().unique().tolist())[:30])

print("\n=== SAMPLE ROWS ===")
print(df[["country", "video_id", "channel_id", "channel_title", "title", "views"]].head(10))

print("\n=== MISSING VALUES ===")
print(df.isna().sum())

print("\n=== UNIQUE COUNTS ===")
print("Unique videos:", df["video_id"].nunique())
print("Unique channels:", df["channel_id"].nunique())