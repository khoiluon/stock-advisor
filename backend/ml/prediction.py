"""
ML Prediction — Load trained ensemble, run inference, tính target_price & stop_loss.

Không import Django, không import ORM.
Input: DataFrame với adjusted OHLCV + features đã tính sẵn.
Output: DataFrame với trend_class, trend_probability, target_price, stop_loss, confidence_score.
"""
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional

from .config import (
    ALL_FEATURES,
    LABEL_MAP_INV,
    MODEL_VERSION,
    MODELS_DIR,
    TBM_ATR_PERIOD,
    TBM_SL_MULTIPLIER,
    TBM_TP_MULTIPLIER,
)
from .training import TrendModelTrainer, load_ensemble
from .utils import prepare_xy


def resolve_key_reasons(
    row: pd.Series,
    trend: str,
    confidence: int,
    proba: dict,
) -> str:
    """
    Ưu tiên key_reasons từ SHAP; fallback chuỗi probability.
    Dùng chung run_ml_predictions / run_daily_prediction.
    """
    if 'key_reasons' in row.index:
        kr = row['key_reasons']
        if pd.notna(kr) and str(kr).strip():
            return str(kr)
    return (
        f"ML Prediction: {trend} ({confidence}% confidence). "
        f"UP: {proba['UP']:.1%}, DOWN: {proba['DOWN']:.1%}, "
        f"SIDEWAY: {proba['SIDEWAY']:.1%}"
    )


def predict_latest(
    df_features: pd.DataFrame,
    models: Optional[List[Dict]] = None,
    version: str = MODEL_VERSION,
    explain: bool = True,
    top_n: int = 3,
) -> pd.DataFrame:
    """
    Chạy inference cho ngày mới nhất của mỗi mã.

    Parameters
    ----------
    df_features : DataFrame đã có đầy đủ features (output của ml/features.py).
                  Phải có columns: stock_id, date, adj_close, atr_14, + features.
    models      : List model artifacts (nếu None thì load từ MODELS_DIR).
    version     : model version để load nếu models=None.

    Returns
    -------
    DataFrame với columns:
        stock_id, date, trend_class, trend_probability, target_price,
        stop_loss, confidence_score, key_reasons (nếu explain=True)
    """
    if models is None:
        models = load_ensemble(MODELS_DIR, version)

    # Lấy ngày mới nhất của mỗi mã
    df_latest = (
        df_features
        .sort_values("date")
        .groupby("stock_id")
        .last()
        .reset_index()
    )

    feature_cols = models[0].get("features") if isinstance(models[0], dict) else None
    if feature_cols is None:
        feature_cols = [f for f in ALL_FEATURES if f in df_latest.columns]

    # Drop rows thiếu adj_close hoặc atr_14 (cần cho target_price/stop_loss).
    # KHÔNG dropna trên toàn bộ feature_cols vì LightGBM/XGBoost xử lý NaN
    # natively (vd: industry luôn NaN nhưng model vẫn predict được).
    essential_cols = ["adj_close", "atr_14"]
    df_valid = df_latest.dropna(subset=[c for c in essential_cols if c in df_latest.columns])
    n_dropped = len(df_latest) - len(df_valid)
    if n_dropped:
        print(f"Dropped {n_dropped} stocks with missing essential features (adj_close, atr_14).")

    X, _ = prepare_xy(df_valid, feature_cols=feature_cols)

    # Ensemble predict
    result = TrendModelTrainer.predict_ensemble(X, models)
    proba = result["proba"]      # (n, 3) — [UP, DOWN, SIDEWAY]
    pred_class = result["pred_class"]

    # Tính target_price và stop_loss từ ATR hiện tại
    atr = df_valid["atr_14"].values
    close = df_valid["adj_close"].values

    target_price = close + TBM_TP_MULTIPLIER * atr
    stop_loss = close - TBM_SL_MULTIPLIER * atr
    confidence = (np.max(proba, axis=1) * 100).astype(int)

    output = pd.DataFrame({
        "stock_id": df_valid["stock_id"].values,
        "date": df_valid["date"].values,
        "adj_close": close,
        "trend_class": [LABEL_MAP_INV[c] for c in pred_class],
        "trend_probability": [
            {"UP": round(float(p[0]), 4), "DOWN": round(float(p[1]), 4), "SIDEWAY": round(float(p[2]), 4)}
            for p in proba
        ],
        "target_price": np.round(target_price, 0),
        "stop_loss": np.round(stop_loss, 0),
        "confidence_score": confidence,
    })

    if explain and models:
        try:
            from .explain import explain_predictions
            shap_df = explain_predictions(
                df_valid, models=models, top_n=top_n,
            )
            output = output.merge(
                shap_df[['stock_id', 'date', 'key_reasons']],
                on=['stock_id', 'date'],
                how='left',
            )
        except Exception as exc:
            print(f"SHAP explanation failed: {exc} — skipping.")
            output['key_reasons'] = ''
    else:
        output['key_reasons'] = ''

    print(
        f"Predictions generated: {len(output)} stocks\n"
        f"  UP: {(output['trend_class']=='UP').sum()}, "
        f"DOWN: {(output['trend_class']=='DOWN').sum()}, "
        f"SIDEWAY: {(output['trend_class']=='SIDEWAY').sum()}"
    )

    return output


def predict_all(
    df_features: pd.DataFrame,
    models: Optional[List[Dict]] = None,
    version: str = MODEL_VERSION,
) -> pd.DataFrame:
    """
    Chạy inference cho TẤT CẢ rows trong df_features.

    Khác với predict_latest() chỉ lấy ngày cuối cùng mỗi mã, hàm này predict
    toàn bộ rows → dùng cho backtest walk-forward (mỗi ngày một tín hiệu).

    Parameters
    ----------
    df_features : DataFrame đã có đầy đủ features (output của ml/features.py).
                  Phải có columns: stock_id, date, adj_close, atr_14, + features.
                  Khuyến nghị: lọc trước bằng chronological_split để chỉ predict
                  trên test set (tiết kiệm thời gian, tránh leak train data vào
                  backtest report).
    models      : List model artifacts (nếu None thì load từ MODELS_DIR).
    version     : model version để load nếu models=None.

    Returns
    -------
    DataFrame với columns:
        stock_id, date, adj_close, adj_open, adj_high, adj_low,
        trend_class, trend_probability, target_price, stop_loss, confidence_score
    """
    if models is None:
        models = load_ensemble(MODELS_DIR, version)

    feature_cols = models[0].get("features") if isinstance(models[0], dict) else None
    if feature_cols is None:
        feature_cols = [f for f in ALL_FEATURES if f in df_features.columns]

    # Drop rows thiếu adj_close hoặc atr_14 (cần cho target_price/stop_loss).
    # Không dropna toàn bộ feature_cols vì model xử lý NaN natively.
    essential_cols = ["adj_close", "atr_14"]
    df_valid = df_features.dropna(
        subset=[c for c in essential_cols if c in df_features.columns]
    ).copy()
    n_dropped = len(df_features) - len(df_valid)
    if n_dropped:
        print(
            f"Dropped {n_dropped:,} rows with missing essential features "
            f"(adj_close, atr_14)."
        )

    X, _ = prepare_xy(df_valid, feature_cols=feature_cols)

    # Ensemble predict
    result = TrendModelTrainer.predict_ensemble(X, models)
    proba = result["proba"]
    pred_class = result["pred_class"]

    atr = df_valid["atr_14"].values
    close = df_valid["adj_close"].values

    target_price = close + TBM_TP_MULTIPLIER * atr
    stop_loss = close - TBM_SL_MULTIPLIER * atr
    confidence = (np.max(proba, axis=1) * 100).astype(int)

    # Giữ thêm OHLC cho backtest (entry mua open T+1, exit intraday TP/SL)
    output_cols = {
        "stock_id": df_valid["stock_id"].values,
        "date": df_valid["date"].values,
        "adj_close": close,
        "trend_class": [LABEL_MAP_INV[c] for c in pred_class],
        "trend_probability": [
            {"UP": round(float(p[0]), 4), "DOWN": round(float(p[1]), 4), "SIDEWAY": round(float(p[2]), 4)}
            for p in proba
        ],
        "target_price": np.round(target_price, 0),
        "stop_loss": np.round(stop_loss, 0),
        "confidence_score": confidence,
    }
    for ohlc_col in ("adj_open", "adj_high", "adj_low"):
        if ohlc_col in df_valid.columns:
            output_cols[ohlc_col] = df_valid[ohlc_col].values

    output = pd.DataFrame(output_cols)

    print(
        f"Predictions generated: {len(output):,} rows / "
        f"{output['stock_id'].nunique()} stocks\n"
        f"  UP: {(output['trend_class']=='UP').sum():,}, "
        f"DOWN: {(output['trend_class']=='DOWN').sum():,}, "
        f"SIDEWAY: {(output['trend_class']=='SIDEWAY').sum():,}"
    )

    return output
