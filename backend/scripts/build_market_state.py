"""
Build Market State — Standalone script, KHÔNG cần Django.

Usage (từ thư mục backend/):
    python scripts/build_market_state.py

Steps:
1. Load features từ data/features/features.parquet
2. Tính market state per ngày (RuleBasedMarketState — Market Breadth)
3. Save ra data/features/market_state.parquet

Cần chạy build_features.py trước.
"""
import sys
from pathlib import Path

# Đảm bảo import được từ backend/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.config import FEATURES_PATH, MARKET_STATE_PATH
from ml.market_state import get_market_state_series
from ml.utils import load_features


def main() -> None:
    print("=" * 60)
    print("STEP 1: Load features")
    print("=" * 60)
    df = load_features(FEATURES_PATH)

    print("\n" + "=" * 60)
    print("STEP 2: Compute market state (Rule-Based Market Breadth)")
    print("=" * 60)
    ms = get_market_state_series(df, use_ml=False)

    print("\n" + "=" * 60)
    print("STEP 3: Save market_state.parquet")
    print("=" * 60)
    Path(MARKET_STATE_PATH).parent.mkdir(parents=True, exist_ok=True)
    ms.to_parquet(MARKET_STATE_PATH, index=False)
    print(f"Saved → {MARKET_STATE_PATH}")

    print("\n--- Summary ---")
    print(f"Shape: {ms.shape}")
    print(f"Date range: {ms['date'].min()} → {ms['date'].max()}")
    print(f"\nState distribution:")
    print(ms['state'].value_counts().to_string())
    print(f"\nConfidence stats:")
    print(ms['confidence'].describe().to_string())
    print(f"\nBreadth stats:")
    print(ms['breadth_pct'].describe().to_string())
    print(f"\nLast 10 days:")
    print(ms.tail(10).to_string(index=False))


if __name__ == "__main__":
    main()
