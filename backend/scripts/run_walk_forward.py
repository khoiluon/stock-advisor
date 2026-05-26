"""Walk-Forward Validation CLI.

Mỗi fold: train ensemble mới (expanding window) → predict → backtest.
Tổng hợp metrics mean ± std — gold standard cho luận văn.

Usage:
    python scripts/run_walk_forward.py
    python scripts/run_walk_forward.py --folds 4
    python scripts/run_walk_forward.py --sample
    python scripts/run_walk_forward.py --confidence 70 --top-k 3
    python scripts/run_walk_forward.py --no-plot
"""
import argparse
import os
import sys
from pathlib import Path
from typing import Optional

os.environ.setdefault('MPLBACKEND', 'Agg')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.config import (  # noqa: E402
    BACKTEST_MIN_CONFIDENCE,
    BACKTEST_TOP_K,
    FEATURES_PATH,
    WF_OUTPUT_DIR,
)
from ml.utils import load_features  # noqa: E402
from ml.walk_forward import (  # noqa: E402
    plot_fold_equity_comparison,
    save_walk_forward_outputs,
    walk_forward_backtest,
)


def main(
    max_folds: Optional[int],
    sample: bool,
    confidence: int,
    top_k: int,
    no_plot: bool,
) -> None:
    print(f"Step 1: Load features ({FEATURES_PATH})")
    df = load_features(FEATURES_PATH)

    if sample:
        sample_stocks = (
            df['stock_id']
            .drop_duplicates()
            .sample(n=min(30, df['stock_id'].nunique()), random_state=42)
            .tolist()
        )
        df = df[df['stock_id'].isin(sample_stocks)].copy()
        print(f"Sample mode: {len(df):,} rows, {len(sample_stocks)} stocks")

    print("\nStep 2-6: Walk-forward backtest (train → predict → backtest per fold)")
    result = walk_forward_backtest(
        df_features=df,
        top_k=top_k,
        min_confidence=confidence,
        max_folds=max_folds,
        verbose=True,
    )

    print("\nStep 7: Save outputs")
    out_dir = save_walk_forward_outputs(result, output_dir=WF_OUTPUT_DIR)

    if not no_plot and result.fold_results:
        print("\nStep 8: Plot equity comparison")
        plot_fold_equity_comparison(
            result,
            save_path=out_dir / 'equity_folds_comparison.png',
        )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Walk-forward ML validation.')
    parser.add_argument(
        '--folds', type=int, default=None,
        help='Gioi han so fold (mac dinh: het data 2021-2024).',
    )
    parser.add_argument(
        '--sample', action='store_true',
        help='30 stocks de test nhanh.',
    )
    parser.add_argument(
        '--confidence', type=int, default=BACKTEST_MIN_CONFIDENCE,
        help=f'Min confidence backtest (default {BACKTEST_MIN_CONFIDENCE}).',
    )
    parser.add_argument(
        '--top-k', type=int, default=BACKTEST_TOP_K,
        help=f'Top-K entries per day (default {BACKTEST_TOP_K}).',
    )
    parser.add_argument(
        '--no-plot', action='store_true',
        help='Bo qua equity comparison plot.',
    )
    args = parser.parse_args()

    main(
        max_folds=args.folds,
        sample=args.sample,
        confidence=args.confidence,
        top_k=args.top_k,
        no_plot=args.no_plot,
    )
