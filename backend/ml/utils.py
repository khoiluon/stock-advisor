"""
ML Utilities — Data loading, train/test split, ensemble sub-sampling, expanding window CV.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Tuple, Generator

from .config import (
    RAW_DATA_PATH,
    FEATURES_PATH,
    TEST_START_DATE,
    NUM_SUBSETS,
    STRIDE,
    EMBARGO_DAYS,
    LABEL_COL,
    ALL_FEATURES,
    NUMERIC_FEATURES,
    CATEGORICAL_FEATURES,
)


def load_raw_data(path: Path = RAW_DATA_PATH) -> pd.DataFrame:
    """Load raw adjusted OHLCV data từ Parquet."""
    if not path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy data file: {path}\n"
            f"Chạy: python manage.py export_ml_data"
        )
    df = pd.read_parquet(path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(['stock_id', 'date']).reset_index(drop=True)
    print(f"Loaded raw data: {df.shape[0]:,} rows, {df['stock_id'].nunique()} stocks")
    return df


def load_features(path: Path = FEATURES_PATH) -> pd.DataFrame:
    """Load computed features từ Parquet."""
    if not path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy features file: {path}\n"
            f"Chạy feature engineering pipeline trước."
        )
    df = pd.read_parquet(path)
    df['date'] = pd.to_datetime(df['date'])
    print(f"Loaded features: {df.shape[0]:,} rows, {df['stock_id'].nunique()} stocks")
    return df


def chronological_split(
    df: pd.DataFrame,
    split_date: str = TEST_START_DATE,
    embargo_days: int = EMBARGO_DAYS,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data theo thời gian — KHÔNG shuffle.
    Train: date < split_date - embargo_days (loại embargo window để tránh TBM label leakage)
    Test:  date >= split_date
    """
    df['date'] = pd.to_datetime(df['date'])
    split_dt = pd.Timestamp(split_date)

    # Embargo: loại EMBARGO_DAYS trading days trước split_date khỏi train set
    # để tránh TBM labels overlap vào test period
    if embargo_days > 0:
        # Tìm các ngày giao dịch duy nhất trước split_date
        dates_before_split = sorted(df.loc[df['date'] < split_dt, 'date'].unique())
        if len(dates_before_split) > embargo_days:
            embargo_start = dates_before_split[-embargo_days]
            mask_train = df['date'] < embargo_start
        else:
            mask_train = df['date'] < split_dt
    else:
        mask_train = df['date'] < split_dt

    mask_test = df['date'] >= split_dt

    df_train = df[mask_train].copy()
    df_test = df[mask_test].copy()

    embargo_info = f" (embargo={embargo_days}d)" if embargo_days > 0 else ""
    print(f"Chronological split @ {split_date}{embargo_info}:")
    print(f"  Train: {len(df_train):,} rows ({df_train['date'].min()} → {df_train['date'].max()})")
    print(f"  Test:  {len(df_test):,} rows ({df_test['date'].min()} → {df_test['date'].max()})")

    return df_train, df_test


def create_sub_datasets(
    df: pd.DataFrame,
    num_subsets: int = NUM_SUBSETS,
    stride: int = STRIDE,
) -> List[pd.DataFrame]:
    """
    Tạo sub-datasets KHÔNG overlapping cho ensemble. Vectorized — O(n).
    Mỗi stock's rows được chia bằng round-robin stride.

    Ví dụ stride=10: row 0 → subset 0, row 1 → subset 1, ..., row 10 → subset 0, ...
    Vì num_subsets == stride == TBM_TIME_LIMIT == 10, mỗi subset có zero label overlap
    giữa các samples kề nhau (khoảng cách stride ≥ TBM forward window).
    """
    if num_subsets != stride:
        raise ValueError(
            f"num_subsets ({num_subsets}) must equal stride ({stride}) "
            f"for zero label overlap guarantee."
        )

    df = df.copy()
    df = df.sort_values(['stock_id', 'date']).reset_index(drop=True)

    # Vectorized: cumcount theo từng stock, mod stride → subset index
    df['_subset_idx'] = df.groupby('stock_id').cumcount() % stride

    result = []
    for i in range(num_subsets):
        sub_df = (
            df[df['_subset_idx'] == i]
            .drop(columns=['_subset_idx'])
            .reset_index(drop=True)
        )
        result.append(sub_df)
        print(f"  Subset {i}: {len(sub_df):,} rows")

    return result


def expanding_window_cv(
    df_train: pd.DataFrame,
    n_folds: int = 3,
    min_train_ratio: float = 0.5,
) -> Generator[Tuple[pd.DataFrame, pd.DataFrame], None, None]:
    """
    Expanding window cross-validation — KHÔNG shuffle, giữ chronological order.

    Fold 1: Train[0 : split_1] → Val[split_1 : split_2]
    Fold 2: Train[0 : split_2] → Val[split_2 : split_3]
    Fold 3: Train[0 : split_3] → Val[split_3 : end]
    """
    dates = sorted(df_train['date'].unique())
    n_dates = len(dates)

    # Tối thiểu min_train_ratio data cho training fold đầu tiên
    min_train_dates = int(n_dates * min_train_ratio)
    remaining = n_dates - min_train_dates
    fold_size = remaining // (n_folds)

    if fold_size < 10:
        raise ValueError(
            f"Không đủ data cho {n_folds} folds. "
            f"Total dates: {n_dates}, min_train: {min_train_dates}"
        )

    for fold in range(n_folds):
        train_end_idx = min_train_dates + fold * fold_size
        val_end_idx = min_train_dates + (fold + 1) * fold_size
        if fold == n_folds - 1:
            val_end_idx = n_dates  # Last fold gets everything remaining

        train_end_date = dates[train_end_idx - 1]
        val_start_date = dates[train_end_idx]
        val_end_date = dates[min(val_end_idx - 1, n_dates - 1)]

        fold_train = df_train[df_train['date'] <= train_end_date]
        fold_val = df_train[
            (df_train['date'] >= val_start_date) & (df_train['date'] <= val_end_date)
        ]

        print(
            f"  Fold {fold + 1}: "
            f"Train {len(fold_train):,} rows (→ {train_end_date.strftime('%Y-%m-%d')}), "
            f"Val {len(fold_val):,} rows ({val_start_date.strftime('%Y-%m-%d')} → {val_end_date.strftime('%Y-%m-%d')})"
        )
        yield fold_train, fold_val


def prepare_xy(
    df: pd.DataFrame,
    feature_cols: List[str] = None,
    label_col: str = LABEL_COL,
) -> Tuple[pd.DataFrame, 'pd.Series | None']:
    """
    Tách X, y từ DataFrame. Handle categorical encoding.
    y = None nếu label_col không có trong df (inference mode).
    """
    if feature_cols is None:
        feature_cols = [f for f in ALL_FEATURES if f in df.columns]

    X = df[feature_cols].copy()

    # Label-encode categorical features (LightGBM/XGBoost handle them natively)
    for col in CATEGORICAL_FEATURES:
        if col in X.columns:
            X[col] = X[col].astype('category').cat.codes

    # Inference mode: label column không tồn tại
    if label_col not in df.columns:
        return X, None

    y = df[label_col].astype(int)

    return X, y
