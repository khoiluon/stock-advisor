"""
Walk-Forward Validation — Retrain ensemble mỗi fold, backtest trên test window.

Khác backtest Day 2 (1 model cố định train 2021-2024, test 2025+):
mỗi fold retrain trên expanding window trong 2021-2024, test ~3 tháng,
tổng hợp metrics mean ± std qua các fold.
"""
from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .backtest import BacktestResult, run_backtest
from .config import (
    BACKTEST_MIN_CONFIDENCE,
    BACKTEST_TOP_K,
    LABEL_COL,
    LABEL_MAP,
    WF_DATA_END,
    WF_DATA_START,
    WF_EMBARGO_DAYS,
    WF_MIN_TRAIN_DAYS,
    WF_OUTPUT_DIR,
    WF_ROLL_STEP_DAYS,
    WF_TEST_WINDOW_DAYS,
)
from .evaluation import evaluate_classification
from .prediction import predict_all
from .training import TrendModelTrainer
from .utils import prepare_xy


@dataclass
class WalkForwardFold:
    """Metadata một fold."""
    fold_id: int
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp
    n_train_rows: int
    n_test_rows: int


@dataclass
class WalkForwardResult:
    """Kết quả walk-forward."""
    folds: List[WalkForwardFold] = field(default_factory=list)
    fold_results: List[BacktestResult] = field(default_factory=list)
    fold_metrics: List[Dict] = field(default_factory=list)
    all_trades: pd.DataFrame = field(default_factory=pd.DataFrame)
    summary: Dict = field(default_factory=dict)


def build_walk_forward_folds(
    trading_dates: pd.DatetimeIndex,
    min_train_days: int = WF_MIN_TRAIN_DAYS,
    test_window_days: int = WF_TEST_WINDOW_DAYS,
    embargo_days: int = WF_EMBARGO_DAYS,
    data_start: str = WF_DATA_START,
    data_end: str = WF_DATA_END,
) -> List[WalkForwardFold]:
    """
    Tạo danh sách fold expanding window.

    Fold 1: train đủ min_train_days, test 60 ngày sau embargo.
    Fold k+1: train mở rộng đến hết test fold trước (expanding), test 60 ngày tiếp.
    """
    start_ts = pd.Timestamp(data_start)
    end_ts = pd.Timestamp(data_end)

    dates = pd.DatetimeIndex(sorted(
        d for d in trading_dates
        if start_ts <= d <= end_ts
    ))
    n = len(dates)
    if n < min_train_days + embargo_days + test_window_days + 1:
        raise ValueError(
            f"Không đủ trading days ({n}) cho walk-forward "
            f"(cần >= {min_train_days + embargo_days + test_window_days + 1})."
        )

    folds: List[WalkForwardFold] = []
    train_end_idx = min_train_days - 1
    fold_id = 0

    while True:
        test_start_idx = train_end_idx + embargo_days + 1
        test_end_idx = test_start_idx + test_window_days - 1
        if test_end_idx >= n:
            break

        folds.append(WalkForwardFold(
            fold_id=fold_id,
            train_start=dates[0],
            train_end=dates[train_end_idx],
            test_start=dates[test_start_idx],
            test_end=dates[test_end_idx],
            n_train_rows=0,
            n_test_rows=0,
        ))

        # Expanding: fold sau train đến hết test fold hiện tại
        train_end_idx = test_end_idx
        fold_id += 1

    return folds


def _fold_precision_up(
    df_test: pd.DataFrame,
    df_predictions: pd.DataFrame,
    models: List[Dict],
) -> Optional[float]:
    """Precision(UP) trên test window nếu có label."""
    if LABEL_COL not in df_test.columns:
        return None

    df_labeled = df_test.dropna(subset=[LABEL_COL]).copy()
    if df_labeled.empty:
        return None

    merged = df_labeled.merge(
        df_predictions[['stock_id', 'date', 'trend_class']],
        on=['stock_id', 'date'],
        how='inner',
    )
    if merged.empty:
        return None

    y_true = merged[LABEL_COL].map(LABEL_MAP).astype(int).values
    y_pred = merged['trend_class'].map(LABEL_MAP).astype(int).values

    metrics = evaluate_classification(y_true, y_pred)
    return float(metrics['precision_up'])


def _aggregate_summary(fold_metrics: List[Dict]) -> Dict:
    """Tính mean ± std cho các metric số."""
    if not fold_metrics:
        return {}

    numeric_keys = set()
    for m in fold_metrics:
        for k, v in m.items():
            if isinstance(v, (int, float)) and not np.isnan(v):
                numeric_keys.add(k)

    summary = {'n_folds': len(fold_metrics)}
    for key in sorted(numeric_keys):
        vals = [m[key] for m in fold_metrics if key in m and m[key] is not None]
        vals = [float(v) for v in vals if not np.isnan(float(v))]
        if vals:
            summary[f'{key}_mean'] = float(np.mean(vals))
            summary[f'{key}_std'] = float(np.std(vals)) if len(vals) > 1 else 0.0

    return summary


def _print_walk_forward_summary(summary: Dict, fold_metrics: List[Dict]) -> None:
    print("\n" + "=" * 60)
    print("WALK-FORWARD SUMMARY (mean ± std)")
    print("=" * 60)
    print(f"  Folds completed: {summary.get('n_folds', 0)}")

    def _fmt(key: str, pct: bool = False, mult: float = 1.0):
        mean_k = f'{key}_mean'
        std_k = f'{key}_std'
        if mean_k not in summary:
            return
        m = summary[mean_k] * mult
        s = summary.get(std_k, 0) * mult
        suffix = '%' if pct else ''
        print(f"  {key:<22}: {m:>8.2f}{suffix} ± {s:.2f}{suffix}")

    _fmt('precision_up', pct=False)
    _fmt('sharpe')
    _fmt('max_drawdown', pct=True, mult=100)
    _fmt('win_rate', pct=True, mult=100)
    _fmt('profit_factor')
    _fmt('total_trades')
    _fmt('total_return', pct=True, mult=100)
    _fmt('cagr', pct=True, mult=100)

    print("\n  Per-fold detail:")
    for i, m in enumerate(fold_metrics):
        tr = m.get('total_return', float('nan'))
        sh = m.get('sharpe', float('nan'))
        pu = m.get('precision_up', float('nan'))
        nt = m.get('total_trades', 0)
        print(
            f"    Fold {i + 1}: return={tr * 100:>6.2f}%  "
            f"sharpe={sh:>5.2f}  precision_up={pu:>5.3f}  trades={int(nt)}"
        )
    print("=" * 60 + "\n")


def walk_forward_backtest(
    df_features: pd.DataFrame,
    train_window_days: int = WF_MIN_TRAIN_DAYS,
    test_window_days: int = WF_TEST_WINDOW_DAYS,
    roll_step_days: int = WF_ROLL_STEP_DAYS,
    embargo_days: int = WF_EMBARGO_DAYS,
    top_k: int = BACKTEST_TOP_K,
    min_confidence: int = BACKTEST_MIN_CONFIDENCE,
    max_folds: Optional[int] = None,
    verbose: bool = True,
    **backtest_kwargs,
) -> WalkForwardResult:
    """
    Walk-forward: mỗi fold train ensemble mới → predict test → backtest.

    Parameters
    ----------
    df_features : toàn bộ features (2021-2024 trong WF_DATA_END).
    train_window_days : số ngày giao dịch tối thiểu cho train fold đầu.
    roll_step_days : không dùng trực tiếp khi expanding (train_end = test_end trước);
                     giữ param để API tương thích spec.
    """
    df = df_features.copy()
    df['date'] = pd.to_datetime(df['date'])

    folds = build_walk_forward_folds(
        df['date'].unique(),
        min_train_days=train_window_days,
        test_window_days=test_window_days,
        embargo_days=embargo_days,
    )
    if max_folds is not None:
        folds = folds[:max_folds]

    if verbose:
        print(f"Walk-forward: {len(folds)} folds "
              f"({WF_DATA_START} → {WF_DATA_END})")

    fold_results: List[BacktestResult] = []
    fold_metrics: List[Dict] = []
    all_trades_list: List[pd.DataFrame] = []

    for fold in folds:
        if verbose:
            print(
                f"\n--- Fold {fold.fold_id + 1}/{len(folds)} ---\n"
                f"  Train: {fold.train_start.date()} → {fold.train_end.date()}\n"
                f"  Test:  {fold.test_start.date()} → {fold.test_end.date()}"
            )

        df_train = df[
            (df['date'] >= fold.train_start) & (df['date'] <= fold.train_end)
        ].copy()
        df_test = df[
            (df['date'] >= fold.test_start) & (df['date'] <= fold.test_end)
        ].copy()

        fold.n_train_rows = len(df_train)
        fold.n_test_rows = len(df_test)

        if df_train.empty or df_test.empty:
            print(f"  Skip fold {fold.fold_id + 1}: empty train or test.")
            continue

        # Train trong temp dir — không ghi đè model v4 chính
        version_tag = f"wf_fold{fold.fold_id}"
        with tempfile.TemporaryDirectory(prefix='wf_train_') as tmp:
            trainer = TrendModelTrainer()
            trainer.models_dir = Path(tmp)
            if verbose:
                print(f"  Training ensemble ({len(df_train):,} rows)...")
            artifacts = trainer.train_ensemble(df_train, version=version_tag)

        if not artifacts:
            print(f"  Skip fold {fold.fold_id + 1}: training produced no models.")
            continue

        if verbose:
            print(f"  Predicting test ({len(df_test):,} rows)...")
        df_predictions = predict_all(df_test, models=artifacts, version=version_tag)

        if verbose:
            print("  Running backtest on test window...")
        bt_result = run_backtest(
            df_features=df_test,
            df_predictions=df_predictions,
            top_k=top_k,
            min_confidence=min_confidence,
            verbose=False,
            **backtest_kwargs,
        )

        metrics = dict(bt_result.metrics)
        metrics['fold_id'] = fold.fold_id
        metrics['train_start'] = str(fold.train_start.date())
        metrics['train_end'] = str(fold.train_end.date())
        metrics['test_start'] = str(fold.test_start.date())
        metrics['test_end'] = str(fold.test_end.date())

        prec_up = _fold_precision_up(df_test, df_predictions, artifacts)
        if prec_up is not None:
            metrics['precision_up'] = prec_up

        fold_results.append(bt_result)
        fold_metrics.append(metrics)

        if not bt_result.trades.empty:
            trades_fold = bt_result.trades.copy()
            trades_fold['fold_id'] = fold.fold_id
            all_trades_list.append(trades_fold)

    all_trades = (
        pd.concat(all_trades_list, ignore_index=True)
        if all_trades_list
        else pd.DataFrame()
    )

    summary = _aggregate_summary(fold_metrics)
    summary['n_folds'] = len(fold_metrics)

    if verbose:
        _print_walk_forward_summary(summary, fold_metrics)

    return WalkForwardResult(
        folds=folds,
        fold_results=fold_results,
        fold_metrics=fold_metrics,
        all_trades=all_trades,
        summary=summary,
    )


def save_walk_forward_outputs(
    result: WalkForwardResult,
    output_dir: Optional[Path] = None,
) -> Path:
    """Lưu trades, metrics per fold, equity curves."""
    output_dir = Path(output_dir or WF_OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not result.all_trades.empty:
        path = output_dir / 'all_trades.parquet'
        result.all_trades.to_parquet(path, index=False)
        print(f"All trades → {path}")

    if result.fold_metrics:
        pd.DataFrame(result.fold_metrics).to_csv(
            output_dir / 'fold_metrics.csv', index=False
        )
        print(f"Fold metrics → {output_dir / 'fold_metrics.csv'}")

    for i, bt in enumerate(result.fold_results):
        if bt.equity_curve is not None and not bt.equity_curve.empty:
            bt.equity_curve.to_csv(output_dir / f'equity_fold_{i + 1}.csv')

    if result.summary:
        pd.Series(result.summary).to_csv(output_dir / 'summary.csv')

    return output_dir


def plot_fold_equity_comparison(
    result: WalkForwardResult,
    save_path: Optional[Path] = None,
) -> None:
    """Overlay equity curves (normalized) của từng fold."""
    import matplotlib.pyplot as plt

    if not result.fold_results:
        return

    plt.figure(figsize=(12, 6))
    for i, bt in enumerate(result.fold_results):
        if bt.equity_curve is None or bt.equity_curve.empty:
            continue
        eq = bt.equity_curve['portfolio_value']
        normalized = eq / eq.iloc[0]
        plt.plot(normalized.index, normalized.values, label=f'Fold {i + 1}', alpha=0.8)

    plt.title('Walk-Forward Equity Curves (normalized per fold)')
    plt.xlabel('Date')
    plt.ylabel('Cumulative return (1 = start)')
    plt.legend(loc='best', fontsize=8)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Equity comparison plot → {save_path}")
    plt.close()
