"""
Build Features Pipeline — Standalone script, KHÔNG cần Django.

Usage (từ thư mục backend/):
    python scripts/build_features.py

Steps:
1. Load raw adjusted OHLCV từ data/raw/ohlcv_adjusted.parquet
2. Tính ~50 features per stock (ml/features.py)
3. Apply Triple Barrier Method labeling (ml/labeling.py)
4. Save ra data/features/features.parquet

Output log sẽ in:
- Shape của dataset
- Phân phối label (UP / DOWN / SIDEWAY %)
- Số stocks bị loại do thiếu data
"""
import sys
from pathlib import Path

# Đảm bảo import được từ backend/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from ml.config import FEATURES_PATH, RAW_DATA_PATH
from ml.features import compute_features
from ml.labeling import create_labeled_dataset
from ml.utils import load_raw_data


def main():
    print("=" * 60)
    print("STEP 1: Load raw data")
    print("=" * 60)
    df = load_raw_data(RAW_DATA_PATH)

    print("\n" + "=" * 60)
    print("STEP 2: Compute features (~50 features per stock)")
    print("=" * 60)
    df_feat = compute_features(df)
    print(f"Features shape: {df_feat.shape}")

    print("\n" + "=" * 60)
    print("STEP 3: Apply Triple Barrier Method labeling")
    print("=" * 60)
    df_labeled = create_labeled_dataset(df_feat)

    print("\n" + "=" * 60)
    print("STEP 4: Save features + labels")
    print("=" * 60)
    Path(FEATURES_PATH).parent.mkdir(parents=True, exist_ok=True)
    df_labeled.to_parquet(FEATURES_PATH, index=False)
    print(f"Saved → {FEATURES_PATH}")

    print("\n--- Summary ---")
    print(f"Shape: {df_labeled.shape}")
    dist = df_labeled["label"].value_counts(normalize=True)
    label_names = {0: "UP", 1: "DOWN", 2: "SIDEWAY"}
    for code, pct in dist.items():
        print(f"  {label_names.get(int(code), code)}: {pct:.1%}")
    print(f"Stocks: {df_labeled['stock_id'].nunique()}")
    print(f"Date range: {df_labeled['date'].min()} → {df_labeled['date'].max()}")


if __name__ == "__main__":
    main()
