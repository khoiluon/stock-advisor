"""ML Portfolio Backtest CLI runner.

Standalone — không import Django ORM. Đọc features + load ensemble + predict
toàn bộ test set + chạy backtest + xuất report.

Usage:
    python scripts/run_backtest.py
    python scripts/run_backtest.py --sample
    python scripts/run_backtest.py --confidence 70 --top-k 5
    python scripts/run_backtest.py --version v3   # so sánh với model cũ
    python scripts/run_backtest.py --no-report    # bỏ qua QuantStats HTML
"""
import argparse
import os
import sys
from pathlib import Path

# Headless matplotlib backend (QuantStats render charts qua matplotlib)
os.environ.setdefault('MPLBACKEND', 'Agg')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.backtest import generate_backtest_report, run_backtest  # noqa: E402
from ml.config import (  # noqa: E402
    BACKTEST_MIN_CONFIDENCE,
    BACKTEST_TOP_K,
    DATA_DIR,
    FEATURES_PATH,
    LABEL_COL,
    MODEL_VERSION,
    MODELS_DIR,
)
from ml.prediction import predict_all  # noqa: E402
from ml.training import load_ensemble  # noqa: E402
from ml.utils import chronological_split, load_features  # noqa: E402


def main(
    sample: bool,
    confidence: int,
    top_k: int,
    version: str,
    no_report: bool,
    start_date: str = '',
    end_date: str = '',
) -> None:
    import pandas as pd

    print(f"Step 1: Load features ({FEATURES_PATH})")
    df = load_features(FEATURES_PATH)

    print("\nStep 2: Chronological split → giữ test set")
    _, df_test = chronological_split(df)

    # Optional date range filter (--start-date, --end-date)
    if start_date:
        df_test = df_test[df_test['date'] >= pd.Timestamp(start_date)]
        print(f"  Filter start: {start_date}")
    if end_date:
        df_test = df_test[df_test['date'] <= pd.Timestamp(end_date)]
        print(f"  Filter end:   {end_date}")

    # Backtest chỉ cần features + OHLCV của test set. KHÔNG cần label
    # (label chỉ dùng cho evaluate_only / training).
    # Giữ rows có cả label NaN — predict_all() handle được.
    if sample:
        # Sample theo stock_id để giữ tính liên tục của chuỗi thời gian
        sample_stocks = (
            df_test['stock_id']
            .drop_duplicates()
            .sample(n=min(50, df_test['stock_id'].nunique()), random_state=42)
            .tolist()
        )
        df_test = df_test[df_test['stock_id'].isin(sample_stocks)].copy()
        print(f"Sample mode: {len(df_test):,} rows, {len(sample_stocks)} stocks")
    else:
        print(f"Full backtest: {len(df_test):,} rows, "
              f"{df_test['stock_id'].nunique()} stocks")

    print(f"\nStep 3: Load model ensemble (version={version})")
    models = load_ensemble(MODELS_DIR, version=version)

    print("\nStep 4: Predict toàn bộ test set")
    df_predictions = predict_all(df_test, models=models, version=version)

    print(
        f"\nStep 5: Run backtest "
        f"(min_confidence={confidence}, top_k={top_k})"
    )
    result = run_backtest(
        df_features=df_test,
        df_predictions=df_predictions,
        min_confidence=confidence,
        top_k=top_k,
        verbose=True,
    )

    if no_report:
        print("Skipped QuantStats report (--no-report).")
    else:
        print("\nStep 6: Generate QuantStats report")
        # Truyền version cho file output → tách v3 / v4
        generate_backtest_report(
            result,
            benchmark_df=None,  # TODO: load VNINDEX khi có data
            output_dir=DATA_DIR / 'backtest',
            version=version,
        )

    # Đảm bảo label NaN không gây nhầm lẫn — chỉ thông báo
    if LABEL_COL in df_test.columns:
        n_na = int(df_test[LABEL_COL].isna().sum())
        if n_na:
            print(
                f"\nNote: {n_na:,} rows trong test set chưa có label "
                f"(warmup ATR / TBM tail / ambiguous) — backtest dùng OHLC "
                f"thực, không phụ thuộc label nên không sao."
            )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run ML portfolio backtest.')
    parser.add_argument(
        '--sample', action='store_true',
        help='Sample 50 stocks cho test nhanh.',
    )
    parser.add_argument(
        '--confidence', type=int, default=BACKTEST_MIN_CONFIDENCE,
        help=f'Min confidence để vào lệnh (default {BACKTEST_MIN_CONFIDENCE}).',
    )
    parser.add_argument(
        '--top-k', type=int, default=BACKTEST_TOP_K,
        help=f'Số mã tối đa mở vị thế mỗi ngày (default {BACKTEST_TOP_K}).',
    )
    parser.add_argument(
        '--version', type=str, default=MODEL_VERSION,
        help=f'Model version để load (default {MODEL_VERSION}).',
    )
    parser.add_argument(
        '--no-report', action='store_true',
        help='Bỏ qua QuantStats HTML report (vẫn xuất CSV).',
    )
    parser.add_argument(
        '--start-date', type=str, default='',
        help='Ngày bắt đầu backtest (vd: 2025-01-01). Mặc định: từ đầu test set.',
    )
    parser.add_argument(
        '--end-date', type=str, default='',
        help='Ngày kết thúc backtest (vd: 2025-12-31). Mặc định: đến cuối data.',
    )
    args = parser.parse_args()

    main(
        sample=args.sample,
        confidence=args.confidence,
        top_k=args.top_k,
        version=args.version,
        no_report=args.no_report,
        start_date=args.start_date,
        end_date=args.end_date,
    )
