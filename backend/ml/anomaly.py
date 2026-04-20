"""
Anomaly Detection — Isolation Forest per-stock + rule-based overlay.

Phát hiện bất thường dựa trên volume, money flow,
và price action patterns cho từng mã riêng biệt.

Design:
- Fit IsolationForest per-stock (mỗi mã có pattern volume khác nhau,
  VCB vs penny stock).
- Rule-based overlay sau IF: phân loại anomaly_type.
- Output: anomaly_score (float, càng âm = càng bất thường),
  is_anomaly (bool), anomaly_type (str).

Không import Django, không import ORM.
"""
import warnings
from pathlib import Path
from typing import Dict, List, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from .config import (
    ANOMALY_FEATURES,
    ANOMALY_RETURN_THRESHOLD,
    ANOMALY_VOLUME_ZSCORE_THRESHOLD,
    ISOLATION_FOREST_PARAMS,
    MODELS_DIR,
)


class AnomalyDetector:
    """
    Isolation Forest per-stock anomaly detector.

    Fit 1 IsolationForest cho mỗi stock_id riêng biệt,
    vì mỗi mã có volume pattern khác nhau.
    Cần tối thiểu MIN_SAMPLES_FIT rows per stock để fit.
    """

    MIN_SAMPLES_FIT: int = 60  # Cần ít nhất 60 rows (~3 tháng) để fit IF

    def __init__(
        self,
        feature_cols: Optional[List[str]] = None,
        if_params: Optional[Dict] = None,
    ) -> None:
        self.feature_cols = feature_cols or ANOMALY_FEATURES
        self.if_params = if_params or ISOLATION_FOREST_PARAMS
        self.models: Dict[str, IsolationForest] = {}
        self._fitted = False

    # ------------------------------------------------------------------
    # Fit
    # ------------------------------------------------------------------
    def fit(self, df: pd.DataFrame) -> "AnomalyDetector":
        """
        Fit IsolationForest per-stock.

        Parameters
        ----------
        df : DataFrame chứa features đã tính.
             Phải có columns: stock_id + self.feature_cols.

        Returns
        -------
        self (fitted)
        """
        self._validate_columns(df)
        stock_ids = df['stock_id'].unique()
        n_fitted = 0
        n_skipped = 0

        n_total = len(stock_ids)

        for idx, sid in enumerate(stock_ids):
            df_stock = df.loc[df['stock_id'] == sid, self.feature_cols].dropna()

            if len(df_stock) < self.MIN_SAMPLES_FIT:
                n_skipped += 1
                continue

            # n_jobs=1, n_estimators=100 per model (data nhỏ per-stock, tránh overhead)
            per_model_params = {
                **self.if_params,
                'n_jobs': 1,
                'n_estimators': min(self.if_params.get('n_estimators', 100), 100),
            }
            model = IsolationForest(**per_model_params)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model.fit(df_stock)

            self.models[sid] = model
            n_fitted += 1

            if (idx + 1) % 200 == 0:
                print(f"  Progress: {idx + 1}/{n_total} stocks...")

        self._fitted = True
        print(
            f"AnomalyDetector fitted: {n_fitted} stocks "
            f"(skipped {n_skipped} with < {self.MIN_SAMPLES_FIT} rows)"
        )
        return self

    # ------------------------------------------------------------------
    # Predict toàn bộ
    # ------------------------------------------------------------------
    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Predict anomaly scores cho toàn bộ rows.

        Parameters
        ----------
        df : DataFrame chứa stock_id + feature_cols + return_1d + volume_zscore_20.

        Returns
        -------
        DataFrame với columns:
            stock_id, date, anomaly_score, is_anomaly, anomaly_type
        """
        self._check_fitted()
        self._validate_columns(df)

        results = []

        for sid, group in df.groupby('stock_id'):
            if sid not in self.models:
                continue

            model = self.models[sid]
            X = group[self.feature_cols].copy()

            # Fill NaN for predict (IF không chấp nhận NaN)
            X = X.fillna(0)

            scores = model.decision_function(X)
            predictions = model.predict(X)  # 1 = normal, -1 = anomaly

            result = pd.DataFrame({
                'stock_id': group['stock_id'].values,
                'date': group['date'].values,
                'anomaly_score': scores,
                'is_anomaly': predictions == -1,
            })

            # Rule-based overlay: phân loại anomaly type
            result['anomaly_type'] = self._classify_anomaly_type(
                group, result['is_anomaly'].values
            )

            results.append(result)

        if not results:
            return pd.DataFrame(
                columns=['stock_id', 'date', 'anomaly_score',
                         'is_anomaly', 'anomaly_type']
            )

        out = pd.concat(results, ignore_index=True)
        n_anomalies = out['is_anomaly'].sum()
        pct = n_anomalies / len(out) * 100 if len(out) > 0 else 0
        print(f"Anomalies detected: {n_anomalies:,} / {len(out):,} ({pct:.1f}%)")
        return out

    # ------------------------------------------------------------------
    # Predict chỉ ngày mới nhất mỗi stock
    # ------------------------------------------------------------------
    def predict_latest(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Predict anomaly cho ngày mới nhất của mỗi stock.

        Parameters
        ----------
        df : DataFrame chứa stock_id, date, feature_cols, return_1d, volume_zscore_20.

        Returns
        -------
        DataFrame chỉ chứa ngày mới nhất mỗi stock.
        """
        self._check_fitted()

        # Lấy ngày mới nhất mỗi mã
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        idx = df.groupby('stock_id')['date'].idxmax()
        df_latest = df.loc[idx].reset_index(drop=True)

        result = self.predict(df_latest)
        print(f"Latest date predictions: {len(result)} stocks")
        return result

    # ------------------------------------------------------------------
    # Save / Load
    # ------------------------------------------------------------------
    def save(self, path: Optional[Path] = None) -> Path:
        """Save tất cả fitted models vào 1 file."""
        self._check_fitted()
        if path is None:
            path = Path(MODELS_DIR) / 'anomaly_detector.joblib'
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            'models': self.models,
            'feature_cols': self.feature_cols,
            'if_params': self.if_params,
        }
        print(f"Saving {len(self.models)} models (compressed)...")
        joblib.dump(payload, path, compress=3)
        size_mb = path.stat().st_size / (1024 * 1024)
        print(f"AnomalyDetector saved → {path} ({size_mb:.1f} MB, {len(self.models)} stocks)")
        return path

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "AnomalyDetector":
        """Load saved AnomalyDetector."""
        if path is None:
            path = Path(MODELS_DIR) / 'anomaly_detector.joblib'
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(
                f"Không tìm thấy anomaly detector: {path}\n"
                f"Chạy: python scripts/detect_anomalies.py --fit"
            )

        payload = joblib.load(path)
        detector = cls(
            feature_cols=payload['feature_cols'],
            if_params=payload['if_params'],
        )
        detector.models = payload['models']
        detector._fitted = True
        print(f"AnomalyDetector loaded ← {path} ({len(detector.models)} stocks)")
        return detector

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _validate_columns(self, df: pd.DataFrame) -> None:
        """Kiểm tra columns cần thiết tồn tại."""
        required = set(self.feature_cols) | {'stock_id'}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(
                f"Thiếu columns: {missing}. "
                f"Cần: stock_id + {self.feature_cols}"
            )

    def _check_fitted(self) -> None:
        if not self._fitted:
            raise RuntimeError(
                "AnomalyDetector chưa fit. "
                "Gọi .fit(df) hoặc AnomalyDetector.load() trước."
            )

    @staticmethod
    def _classify_anomaly_type(
        df_stock: pd.DataFrame,
        is_anomaly: np.ndarray,
    ) -> List[str]:
        """
        Rule-based overlay: phân loại anomaly type.

        - volume_spike: volume_zscore_20 > 3 VÀ |return_1d| > 3%
        - money_flow_abnormal: các trường hợp anomaly còn lại
        - normal: không phải anomaly
        """
        types: List[str] = []

        # Lấy giá trị nếu có, không thì mặc định 0
        vol_zscore = (
            df_stock['volume_zscore_20'].values
            if 'volume_zscore_20' in df_stock.columns
            else np.zeros(len(df_stock))
        )
        returns = (
            df_stock['return_1d'].values
            if 'return_1d' in df_stock.columns
            else np.zeros(len(df_stock))
        )

        for i in range(len(is_anomaly)):
            if not is_anomaly[i]:
                types.append('normal')
            elif (
                abs(vol_zscore[i]) > ANOMALY_VOLUME_ZSCORE_THRESHOLD
                and abs(returns[i]) > ANOMALY_RETURN_THRESHOLD
            ):
                types.append('volume_spike')
            else:
                types.append('money_flow_abnormal')

        return types
