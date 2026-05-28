"""
ML Training Pipeline — Train LightGBM/XGBoost ensemble trên 10 sub-datasets.

Không import Django, không import ORM.
Input/Output: numpy arrays, DataFrames, joblib files.
"""
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple

from lightgbm import LGBMClassifier
from xgboost import XGBClassifier

from .config import (
    ALL_FEATURES,
    CATEGORICAL_FEATURES,
    CLASS_WEIGHTS,
    LABEL_COL,
    LABEL_MAP,
    LGBM_PARAMS,
    MODEL_VERSION,
    MODELS_DIR,
    NUM_SUBSETS,
    STRIDE,
    XGB_PARAMS,
)
from .utils import create_sub_datasets, prepare_xy


class TrendModelTrainer:
    """Train LightGBM + XGBoost ensemble trên 10 non-overlapping sub-datasets (stride=10)."""

    def __init__(self):
        self.models_dir = Path(MODELS_DIR)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.feature_cols: List[str] = []

    # ------------------------------------------------------------------
    # Single model
    # ------------------------------------------------------------------
    def train_single_model(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        algo: str = "lightgbm",
    ):
        """Train 1 model. Return fitted model."""
        if algo == "lightgbm":
            cat_cols = [c for c in CATEGORICAL_FEATURES if c in X_train.columns]
            model = LGBMClassifier(**LGBM_PARAMS)
            model.fit(
                X_train,
                y_train,
                categorical_feature=cat_cols if cat_cols else "auto",
            )
        elif algo == "xgboost":
            params = {k: v for k, v in XGB_PARAMS.items() if k != "use_label_encoder"}
            model = XGBClassifier(**params)
            sw = np.array([CLASS_WEIGHTS[int(yi)] for yi in y_train])
            model.fit(X_train, y_train, sample_weight=sw)
        else:
            raise ValueError(f"Unknown algo: {algo}. Use 'lightgbm' or 'xgboost'.")

        return model

    # ------------------------------------------------------------------
    # Full ensemble pipeline
    # ------------------------------------------------------------------
    def train_ensemble(
        self,
        df_labeled: pd.DataFrame,
        version: str = MODEL_VERSION,
    ) -> List[Dict]:
        """
        Full train pipeline:
        1. Tạo 10 non-overlapping sub-datasets (stride=10, zero label overlap)
        2. Train LightGBM + XGBoost trên mỗi sub-dataset → 20 models tổng
        3. Save mỗi model + metadata vào MODELS_DIR
        4. Return list[dict] với model artifacts

        Parameters
        ----------
        df_labeled : DataFrame đã có features + label column
        version    : version string dùng trong filename (e.g., "v1")

        Returns
        -------
        List of dicts: [{'model': fitted_model, 'algo': str, 'subset': int, 'path': Path}]
        """
        # Validate input
        if LABEL_COL not in df_labeled.columns:
            raise ValueError(f"Missing label column '{LABEL_COL}' in DataFrame.")

        # Xác định feature columns
        available = [f for f in ALL_FEATURES if f in df_labeled.columns]
        self.feature_cols = available
        print(f"Features used: {len(available)} / {len(ALL_FEATURES)}")

        # Tạo 10 sub-datasets (stride=10 = TBM_TIME_LIMIT → zero label overlap)
        print(f"\nCreating {NUM_SUBSETS} sub-datasets (stride={STRIDE})...")
        subsets = create_sub_datasets(df_labeled, NUM_SUBSETS, STRIDE)

        artifacts = []

        for i, sub_df in enumerate(subsets):
            # Drop rows với label NaN (cuối mỗi stock do TBM)
            sub_df = sub_df.dropna(subset=[LABEL_COL])
            if len(sub_df) == 0:
                print(f"  Subset {i}: empty after dropna, skip.")
                continue

            X, y = prepare_xy(sub_df, feature_cols=self.feature_cols)

            for algo in ("lightgbm", "xgboost"):
                print(f"  Training {algo} on subset {i} ({len(X):,} samples)...")
                model = self.train_single_model(X, y, algo=algo)

                fname = f"{algo}_d{i}_{version}.joblib"
                save_path = self.models_dir / fname
                payload = {
                    "model": model,
                    "features": self.feature_cols,
                    "label_map": LABEL_MAP,
                    "algo": algo,
                    "subset": i,
                    "version": version,
                    "n_train": len(X),
                }
                joblib.dump(payload, save_path)
                print(f"    Saved → {save_path}")

                artifacts.append({"model": model, "features": self.feature_cols, "algo": algo, "subset": i, "path": save_path})

        print(f"\nEnsemble training complete: {len(artifacts)} models trained.")
        return artifacts

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------
    @staticmethod
    def predict_ensemble(
        X: pd.DataFrame,
        models: List[Dict],
    ) -> Dict[str, np.ndarray]:
        """
        Average prediction probability qua tất cả models trong ensemble.

        Returns
        -------
        dict với keys: 'proba' (n_samples × 3), 'pred_class' (n_samples,)
        Class order: 0=UP, 1=DOWN, 2=SIDEWAY  (theo LABEL_MAP)
        """
        if not models:
            raise ValueError("No models provided for ensemble prediction.")

        try:
            from threadpoolctl import threadpool_limits
            ctx = threadpool_limits(limits=4)
        except ImportError:
            from contextlib import nullcontext
            ctx = nullcontext()

        proba_sum = np.zeros((len(X), 3))

        # Giới hạn 4 threads để tránh OMP deadlock khi gọi nhiều models tuần tự
        with ctx:
            for artifact in models:
                m = artifact["model"] if isinstance(artifact, dict) else artifact
                p = m.predict_proba(X)
                # Đảm bảo 3 classes (guard nếu model thiếu class)
                if p.shape[1] < 3:
                    full = np.zeros((len(X), 3))
                    for j, cls in enumerate(m.classes_):
                        full[:, cls] = p[:, j]
                    p = full
                proba_sum += p

        proba_avg = proba_sum / len(models)
        pred_class = np.argmax(proba_avg, axis=1)

        return {"proba": proba_avg, "pred_class": pred_class}


# ------------------------------------------------------------------
# Convenience: load saved ensemble từ MODELS_DIR
# ------------------------------------------------------------------
def load_ensemble(models_dir: Path = MODELS_DIR, version: str = MODEL_VERSION) -> List[Dict]:
    """Load tất cả model files matching version từ MODELS_DIR."""
    models_dir = Path(models_dir)
    pattern = f"*_{version}.joblib"
    files = sorted(models_dir.glob(pattern))
    if not files:
        raise FileNotFoundError(
            f"Không tìm thấy model files '{pattern}' trong {models_dir}.\n"
            f"Chạy train pipeline trước."
        )
    artifacts = []
    for f in files:
        payload = joblib.load(f)
        artifacts.append(payload)
        print(f"  Loaded: {f.name}")
    print(f"Loaded {len(artifacts)} models from {models_dir}")
    return artifacts
