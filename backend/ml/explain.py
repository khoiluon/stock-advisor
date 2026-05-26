"""
SHAP-based prediction explanations for LightGBM ensemble (subset d0).

Dùng TreeExplainer — tối ưu cho tree models, nhanh hơn KernelExplainer.
Chỉ phân tích class UP (index 0) vì đó là tín hiệu quan tâm cho advisory.
"""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .utils import prepare_xy

# Ánh xạ tên feature kỹ thuật → hiển thị (tiếng Việt / ngắn gọn)
FEATURE_DISPLAY_NAMES: Dict[str, str] = {
    # TREND
    'sma_20': 'SMA(20)',
    'sma_50': 'SMA(50)',
    'sma_150': 'SMA(150)',
    'price_vs_sma20': 'Giá vs SMA20',
    'price_vs_sma50': 'Giá vs SMA50',
    'price_vs_sma150': 'Giá vs SMA150',
    'sma_cross_20_50': 'Giao cắt SMA20/50',
    'sma_cross_50_150': 'Giao cắt SMA50/150',
    'adx_14': 'ADX(14)',
    'bb_percent': '% Bollinger',
    'bb_width': 'Độ rộng Bollinger',
    'close_vs_52w_high': 'Gần đỉnh 52 tuần',
    # MOMENTUM
    'rsi_14': 'RSI(14)',
    'macd_hist': 'MACD Histogram',
    'macd_hist_diff': 'MACD Hist Change',
    'stoch_k': 'Stochastic %K',
    'stoch_d': 'Stochastic %D',
    'williams_r': 'Williams %R',
    'roc_10': 'ROC(10)',
    # VOLUME
    'rvol': 'Khối lượng tương đối',
    'obv': 'OBV',
    'obv_change_5': 'OBV Change 5d',
    'cmf_20': 'CMF(20)',
    'cmf_trend': 'Xu hướng CMF',
    'mfi_14': 'MFI(14)',
    'volume_zscore_20': 'Volume Z-score',
    'trade_value_zscore': 'GTGD Z-score',
    # PRICE ACTION
    'return_1d': 'Lợi suất 1 ngày',
    'return_3d': 'Lợi suất 3 ngày',
    'return_5d': 'Lợi suất 5 ngày',
    'return_10d': 'Lợi suất 10 ngày',
    'return_20d': 'Lợi suất 20 ngày',
    'volatility_10d': 'Biến động 10 ngày',
    'volatility_20d': 'Biến động 20 ngày',
    'atr_14': 'ATR(14)',
    'atr_percent': 'ATR %',
    'high_low_range': 'Biên độ High-Low',
    'gap_percent': '% Gap',
    'upper_shadow_ratio': 'Bóng nến trên',
    'lower_shadow_ratio': 'Bóng nến dưới',
    # LAG
    'rsi_lag_1': 'RSI lag 1d',
    'rsi_lag_3': 'RSI lag 3d',
    'rsi_lag_5': 'RSI lag 5d',
    'macd_hist_lag_1': 'MACD lag 1d',
    'macd_hist_lag_3': 'MACD lag 3d',
    'macd_hist_lag_5': 'MACD lag 5d',
    'return_lag_1': 'Lợi suất lag 1d',
    'return_lag_3': 'Lợi suất lag 3d',
    'return_lag_5': 'Lợi suất lag 5d',
    'volume_zscore_lag_1': 'Vol Z-score lag 1d',
    'volume_zscore_lag_3': 'Vol Z-score lag 3d',
    # WARNING
    'days_zero_volume': 'Ngày không GD',
    'price_below_par': 'Giá dưới mệnh giá',
    'avg_volume_decline': 'KL giảm dần',
    # CATEGORICAL
    'exchange': 'Sàn',
    'industry': 'Ngành',
    'day_of_week': 'Thứ trong tuần',
    'month': 'Tháng',
}


def _extract_shap_up_matrix(shap_values, n_samples: int, n_features: int) -> np.ndarray:
    """Chuẩn hóa output SHAP multiclass về (n_samples, n_features) cho class UP."""
    if isinstance(shap_values, list):
        # LightGBM multiclass: list len=3, mỗi phần (n, features)
        return np.asarray(shap_values[0])
    arr = np.asarray(shap_values)
    if arr.ndim == 3:
        # (n_samples, n_features, n_classes)
        return arr[:, :, 0]
    if arr.ndim == 2:
        return arr
    raise ValueError(f"Unexpected SHAP shape: {arr.shape}")


def explain_predictions(
    df_features: pd.DataFrame,
    models: List[Dict],
    top_n: int = 3,
    subset_idx: int = 0,
) -> pd.DataFrame:
    """
    SHAP TreeExplainer cho 1 LightGBM model (subset d0).

    Returns DataFrame: stock_id, date, shap_top_features, shap_top_values, key_reasons
    key_reasons format: "RSI(14) (35%) | Volume Z-score (30%) | ..."
    """
    import shap

    lgbm = next(
        (
            a for a in models
            if a.get('algo') == 'lightgbm' and a.get('subset') == subset_idx
        ),
        None,
    )
    if lgbm is None:
        # Thử load từ payload joblib (subset field có thể là int)
        lgbm = next(
            (a for a in models if a.get('algo') == 'lightgbm'),
            None,
        )
    if lgbm is None:
        raise ValueError(f"Không tìm thấy lightgbm_d{subset_idx} trong models.")

    feature_cols = lgbm['features']
    df_work = df_features.reset_index(drop=True)

    X, _ = prepare_xy(df_work, feature_cols=feature_cols)

    explainer = shap.TreeExplainer(lgbm['model'])
    shap_values = explainer.shap_values(X)
    shap_up = _extract_shap_up_matrix(shap_values, len(X), len(feature_cols))

    results = []
    for i in range(len(df_work)):
        row_shap = shap_up[i]
        top_idx = np.argsort(np.abs(row_shap))[-top_n:][::-1]
        top_feats = [feature_cols[j] for j in top_idx]
        top_vals = row_shap[top_idx]

        total = float(np.abs(top_vals).sum())
        if total > 0:
            pcts = np.abs(top_vals) / total * 100
        else:
            pcts = np.zeros(top_n)

        reasons = [
            f"{FEATURE_DISPLAY_NAMES.get(f, f)} ({p:.0f}%)"
            for f, p in zip(top_feats, pcts)
        ]

        results.append({
            'stock_id': df_work.loc[i, 'stock_id'],
            'date': df_work.loc[i, 'date'],
            'shap_top_features': top_feats,
            'shap_top_values': top_vals.tolist(),
            'key_reasons': ' | '.join(reasons),
        })

    return pd.DataFrame(results)
