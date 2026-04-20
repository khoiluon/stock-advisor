"""
Optuna Hyperparameter Tuning — Tối ưu Precision(UP) cho LightGBM & XGBoost ensemble.

Không import Django, không import ORM.
Input: features.parquet → Expanding Window CV trên train set (2021-2024).
Output: best params → config override → retrain final ensemble.

Usage:
    python scripts/tune_hyperparams.py [--n-trials 50] [--timeout 3600]
"""
import optuna
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from typing import Dict, Optional, Tuple

from lightgbm import LGBMClassifier
from xgboost import XGBClassifier
from sklearn.metrics import precision_score

from .config import (
    ALL_FEATURES,
    CATEGORICAL_FEATURES,
    FEATURES_PATH,
    LABEL_COL,
    LABEL_MAP,
    MODELS_DIR,
    NUM_SUBSETS,
    STRIDE,
)
from .utils import (
    chronological_split,
    create_sub_datasets,
    expanding_window_cv,
    load_features,
    prepare_xy,
)


# Suppress Optuna info-level logs (only warnings/errors)
optuna.logging.set_verbosity(optuna.logging.WARNING)


def _train_and_eval_single(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    algo: str,
    params: Dict,
) -> float:
    """Train single model, return Precision(UP) on validation set."""
    if algo == "lightgbm":
        cat_cols = [c for c in CATEGORICAL_FEATURES if c in X_train.columns]
        model = LGBMClassifier(**params, verbose=-1, n_jobs=1)
        model.fit(X_train, y_train, categorical_feature=cat_cols if cat_cols else "auto")
    else:
        model = XGBClassifier(**params, verbosity=0, n_jobs=1)
        model.fit(X_train, y_train)

    y_pred = model.predict(X_val)
    # Precision(UP) = precision for class 0 (UP)
    return precision_score(y_val, y_pred, labels=[0], average="macro", zero_division=0)


def _suggest_lgbm_params(trial: optuna.Trial) -> Dict:
    """Suggest LightGBM hyperparameters. Giảm complexity cho 407 stocks."""
    return {
        "num_leaves": trial.suggest_int("lgbm_num_leaves", 15, 63),
        "max_depth": trial.suggest_int("lgbm_max_depth", 4, 10),
        "learning_rate": trial.suggest_float("lgbm_lr", 0.01, 0.15, log=True),
        "n_estimators": trial.suggest_int("lgbm_n_estimators", 100, 600, step=50),
        "min_child_samples": trial.suggest_int("lgbm_min_child_samples", 20, 150),
        "subsample": trial.suggest_float("lgbm_subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("lgbm_colsample", 0.5, 1.0),
        "reg_alpha": trial.suggest_float("lgbm_reg_alpha", 1e-3, 10.0, log=True),
        "reg_lambda": trial.suggest_float("lgbm_reg_lambda", 1e-3, 10.0, log=True),
        "class_weight": "balanced",
        "random_state": 42,
    }


def _suggest_xgb_params(trial: optuna.Trial) -> Dict:
    """Suggest XGBoost hyperparameters."""
    return {
        "max_depth": trial.suggest_int("xgb_max_depth", 4, 10),
        "learning_rate": trial.suggest_float("xgb_lr", 0.01, 0.15, log=True),
        "n_estimators": trial.suggest_int("xgb_n_estimators", 100, 600, step=50),
        "min_child_weight": trial.suggest_int("xgb_min_child_weight", 20, 150),
        "subsample": trial.suggest_float("xgb_subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("xgb_colsample", 0.5, 1.0),
        "reg_alpha": trial.suggest_float("xgb_reg_alpha", 1e-3, 10.0, log=True),
        "reg_lambda": trial.suggest_float("xgb_reg_lambda", 1e-3, 10.0, log=True),
        "eval_metric": "mlogloss",
        "random_state": 42,
    }


class OptunaObjective:
    """
    Objective function: train ensemble trên 1 sub-dataset (D_0) với expanding window CV.
    Maximize mean Precision(UP) across 3 folds.
    Dùng 1 sub-dataset thay vì 10 để giảm thời gian tuning ~10×.
    """

    def __init__(self, df_train: pd.DataFrame, feature_cols: list, algo: str = "lightgbm"):
        self.algo = algo
        self.feature_cols = feature_cols

        # Chỉ dùng 1 sub-dataset (D_0) để tune nhanh
        # Vẫn đại diện vì data đã được stride-sampled đều
        subsets = create_sub_datasets(df_train, NUM_SUBSETS, STRIDE)
        self.sub_df = subsets[0].dropna(subset=[LABEL_COL])
        print(f"  Tuning on subset D_0: {len(self.sub_df):,} rows")

    def __call__(self, trial: optuna.Trial) -> float:
        if self.algo == "lightgbm":
            params = _suggest_lgbm_params(trial)
        else:
            params = _suggest_xgb_params(trial)

        precisions = []
        for fold_train, fold_val in expanding_window_cv(self.sub_df, n_folds=3):
            X_train, y_train = prepare_xy(fold_train, self.feature_cols)
            X_val, y_val = prepare_xy(fold_val, self.feature_cols)

            if y_train is None or y_val is None:
                continue

            try:
                p_up = _train_and_eval_single(
                    X_train, y_train, X_val, y_val, self.algo, params
                )
                precisions.append(p_up)
            except Exception as e:
                print(f"  Trial {trial.number} fold error: {e}")
                return 0.0

        if not precisions:
            return 0.0

        return float(np.mean(precisions))


def run_optuna_tuning(
    n_trials: int = 50,
    timeout: Optional[int] = None,
    algo: str = "both",
) -> Dict:
    """
    Run Optuna tuning cho LightGBM và/hoặc XGBoost.

    Parameters
    ----------
    n_trials : số trials mỗi algorithm
    timeout  : max seconds (None = no limit)
    algo     : 'lightgbm', 'xgboost', or 'both'

    Returns
    -------
    dict: {'lightgbm': {'best_params': ..., 'best_value': ...}, 'xgboost': {...}}
    """
    print("=" * 60)
    print("Loading features & splitting data...")
    print("=" * 60)
    df = load_features(FEATURES_PATH)
    df_train, df_test = chronological_split(df)

    feature_cols = [f for f in ALL_FEATURES if f in df.columns]
    print(f"Features: {len(feature_cols)}")

    results = {}
    algos = []
    if algo in ("lightgbm", "both"):
        algos.append("lightgbm")
    if algo in ("xgboost", "both"):
        algos.append("xgboost")

    for alg in algos:
        print(f"\n{'=' * 60}")
        print(f"Tuning {alg.upper()} ({n_trials} trials)")
        print("=" * 60)

        objective = OptunaObjective(df_train, feature_cols, algo=alg)

        study = optuna.create_study(
            direction="maximize",
            study_name=f"stockadvisor_{alg}",
            sampler=optuna.samplers.TPESampler(seed=42),
            pruner=optuna.pruners.MedianPruner(n_warmup_steps=5),
        )
        study.optimize(
            objective,
            n_trials=n_trials,
            timeout=timeout,
            show_progress_bar=True,
            n_jobs=1,
        )

        print(f"\n--- {alg.upper()} Best Trial ---")
        print(f"  Value (mean Precision(UP)): {study.best_value:.4f}")
        print(f"  Params: {study.best_params}")

        results[alg] = {
            "best_params": study.best_params,
            "best_value": study.best_value,
            "study": study,
        }

    # Save results
    save_path = Path(MODELS_DIR) / "optuna_results.joblib"
    save_data = {
        alg: {"best_params": r["best_params"], "best_value": r["best_value"]}
        for alg, r in results.items()
    }
    joblib.dump(save_data, save_path)
    print(f"\nResults saved → {save_path}")

    return results


def retrain_with_best_params(
    optuna_results: Optional[Dict] = None,
    version: str = "v2",
) -> None:
    """
    Retrain full ensemble (20 models) dùng best params từ Optuna.
    Evaluate trên holdout test set 2025+.
    """
    from .training import TrendModelTrainer
    from .evaluation import evaluate_ensemble, plot_confusion_matrix, plot_feature_importance

    # Load Optuna results nếu chưa có
    if optuna_results is None:
        results_path = Path(MODELS_DIR) / "optuna_results.joblib"
        if not results_path.exists():
            raise FileNotFoundError(
                f"Không tìm thấy {results_path}. Chạy run_optuna_tuning() trước."
            )
        optuna_results = joblib.load(results_path)

    # Build final params
    lgbm_best = _extract_algo_params(optuna_results.get("lightgbm", {}), "lgbm")
    xgb_best = _extract_algo_params(optuna_results.get("xgboost", {}), "xgb")

    print("=" * 60)
    print(f"Retrain ensemble {version} with best Optuna params")
    print("=" * 60)
    print(f"LightGBM params: {lgbm_best}")
    print(f"XGBoost params:  {xgb_best}")

    # Load data
    df = load_features(FEATURES_PATH)
    df_train, df_test = chronological_split(df)
    feature_cols = [f for f in ALL_FEATURES if f in df.columns]

    # Override config params temporarily for training
    import ml.config as cfg
    original_lgbm = cfg.LGBM_PARAMS.copy()
    original_xgb = cfg.XGB_PARAMS.copy()

    cfg.LGBM_PARAMS.update(lgbm_best)
    cfg.XGB_PARAMS.update(xgb_best)

    try:
        trainer = TrendModelTrainer()
        artifacts = trainer.train_ensemble(df_train, version=version)

        # Evaluate
        if len(df_test) > 0:
            print(f"\n{'=' * 60}")
            print(f"Evaluate {version} on holdout test set")
            print("=" * 60)
            df_test_clean = df_test.dropna(subset=[LABEL_COL])
            X_test, y_test = prepare_xy(df_test_clean, feature_cols=feature_cols)
            metrics = evaluate_ensemble(artifacts, X_test, y_test)

            # Save plots
            plots_dir = Path(MODELS_DIR).parent / "plots"
            plots_dir.mkdir(parents=True, exist_ok=True)
            plot_confusion_matrix(
                y_test.values,
                metrics["ensemble_pred"],
                save_path=plots_dir / f"confusion_matrix_{version}.png",
            )
            lgbm_artifact = next((a for a in artifacts if a.get("algo") == "lightgbm"), None)
            if lgbm_artifact:
                plot_feature_importance(
                    lgbm_artifact["model"],
                    feature_cols,
                    save_path=plots_dir / f"feature_importance_{version}.png",
                )

            print(f"\n{'=' * 60}")
            print(f"SUMMARY: {version}")
            print(f"  Precision(UP): {metrics['precision_up']:.4f}")
            if metrics.get('logloss'):
                print(f"  Log-loss:      {metrics['logloss']:.4f}")
            print("=" * 60)
        else:
            print("Warning: test set empty — no 2025+ data yet.")

    finally:
        # Restore original config
        cfg.LGBM_PARAMS.update(original_lgbm)
        cfg.XGB_PARAMS.update(original_xgb)


def _extract_algo_params(result: Dict, prefix: str) -> Dict:
    """
    Extract algo-specific params from Optuna best_params.
    Optuna names them like 'lgbm_num_leaves' → strip prefix → 'num_leaves'.
    """
    best_params = result.get("best_params", {})
    extracted = {}
    for key, val in best_params.items():
        if key.startswith(prefix + "_"):
            clean_key = key[len(prefix) + 1:]
            # Map back to original param names
            param_map = {
                "lr": "learning_rate",
                "colsample": "colsample_bytree",
                "min_child_samples": "min_child_samples",
                "min_child_weight": "min_child_weight",
            }
            clean_key = param_map.get(clean_key, clean_key)
            extracted[clean_key] = val

    # Add fixed params
    if prefix == "lgbm":
        extracted.setdefault("class_weight", "balanced")
        extracted.setdefault("random_state", 42)
        extracted.setdefault("verbose", -1)
        extracted.setdefault("n_jobs", -1)
    elif prefix == "xgb":
        extracted.setdefault("random_state", 42)
        extracted.setdefault("verbosity", 0)
        extracted.setdefault("n_jobs", -1)
        extracted.setdefault("eval_metric", "mlogloss")

    return extracted
