"""
Evaluate ensemble trên holdout test set (2025+).
Dùng models đã train sẵn — không train lại.

Usage:
    python scripts/evaluate_only.py           # full test set
    python scripts/evaluate_only.py --sample  # 10k rows để test nhanh
"""
import sys
import os
# Headless backend trước khi matplotlib được import bất kỳ đâu
os.environ.setdefault("MPLBACKEND", "Agg")

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import pandas as pd
from ml.config import FEATURES_PATH, MODELS_DIR, LABEL_COL, MODEL_VERSION
from ml.evaluation import evaluate_classification, plot_confusion_matrix, plot_feature_importance
from ml.training import TrendModelTrainer, load_ensemble
from ml.utils import chronological_split, load_features, prepare_xy


def main(sample: bool = False):
    print("Loading features...")
    df = load_features(FEATURES_PATH)
    _, df_test = chronological_split(df)
    df_test_clean = df_test.dropna(subset=[LABEL_COL])

    if sample:
        df_test_clean = df_test_clean.sample(n=min(10_000, len(df_test_clean)), random_state=42)
        print(f"Sample mode: {len(df_test_clean):,} rows")
    else:
        print(f"Full test: {len(df_test_clean):,} rows")

    print(f"Loading models (version={MODEL_VERSION})...")
    artifacts = load_ensemble(MODELS_DIR, version=MODEL_VERSION)
    feature_cols = artifacts[0]["features"]

    X_test, y_test = prepare_xy(df_test_clean, feature_cols=feature_cols)

    print("Running ensemble inference (n_jobs=1 per model)...")
    result = TrendModelTrainer.predict_ensemble(X_test, artifacts)
    proba = result["proba"]
    pred = result["pred_class"]

    metrics = evaluate_classification(y_test.values, pred, proba)
    print("\n" + metrics["report_str"])
    print(f"Precision(UP): {metrics['precision_up']:.4f}")
    if metrics.get("logloss"):
        print(f"Log-loss:      {metrics['logloss']:.4f}")

    plots_dir = Path(MODELS_DIR).parent / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    plot_confusion_matrix(
        y_test.values, pred,
        save_path=plots_dir / f"confusion_matrix_{MODEL_VERSION}.png",
    )
    lgbm = next((a for a in artifacts if a.get("algo") == "lightgbm"), None)
    if lgbm:
        plot_feature_importance(
            lgbm["model"],
            feature_names=feature_cols,
            top_n=20,
            save_path=plots_dir / f"feature_importance_{MODEL_VERSION}.png",
        )
    print(f"\nPlots saved → {plots_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", action="store_true", help="Use 10k sample for quick test")
    args = parser.parse_args()
    main(sample=args.sample)
