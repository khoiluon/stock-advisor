"""
Train Pipeline — Standalone script, KHÔNG cần Django.

Usage (từ thư mục backend/):
    python scripts/train_pipeline.py

Steps:
1. Load features từ data/features/features.parquet
2. Chronological split: train 2021-2024 (embargo 10d), test 2025+
3. Train ensemble 20 models (10 sub-datasets × LightGBM + XGBoost, stride=10)
4. Evaluate trên holdout test set
5. Save confusion matrix và feature importance plot

Cần chạy build_features.py trước.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from ml.config import FEATURES_PATH, MODELS_DIR
from ml.evaluation import evaluate_ensemble, plot_confusion_matrix, plot_feature_importance
from ml.training import TrendModelTrainer
from ml.utils import chronological_split, load_features


def main():
    print("=" * 60)
    print("STEP 1: Load features")
    print("=" * 60)
    df = load_features(FEATURES_PATH)

    print("\n" + "=" * 60)
    print("STEP 2: Chronological split")
    print("=" * 60)
    df_train, df_test = chronological_split(df)

    print("\n" + "=" * 60)
    print("STEP 3: Train ensemble (20 models = 10 subsets × 2 algos)")
    print("=" * 60)
    trainer = TrendModelTrainer()
    artifacts = trainer.train_ensemble(df_train, version="v1")

    print("\n" + "=" * 60)
    print("STEP 4: Evaluate on holdout test set (2025+)")
    print("=" * 60)
    if len(df_test) == 0:
        print("Warning: test set empty — no 2025+ data yet.")
        return

    from ml.utils import prepare_xy
    from ml.config import LABEL_COL

    df_test_clean = df_test.dropna(subset=[LABEL_COL])
    feature_cols = artifacts[0]["features"] if artifacts else trainer.feature_cols
    X_test, y_test = prepare_xy(df_test_clean, feature_cols=feature_cols)

    metrics = evaluate_ensemble(artifacts, X_test, y_test)

    # Save plots
    plots_dir = Path(MODELS_DIR).parent / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    plot_confusion_matrix(
        y_test.values,
        metrics["ensemble_pred"],
        save_path=plots_dir / "confusion_matrix_v1.png",
    )

    # Feature importance từ model đầu tiên LightGBM
    lgbm_artifact = next((a for a in artifacts if a.get("algo") == "lightgbm"), None)
    if lgbm_artifact:
        plot_feature_importance(
            lgbm_artifact["model"],
            feature_names=feature_cols,
            top_n=20,
            save_path=plots_dir / "feature_importance_v1.png",
        )

    print(f"\n=== Final Result ===")
    print(f"Precision(UP): {metrics['precision_up']:.4f}")
    print(f"Models saved in: {MODELS_DIR}")
    print(f"Plots saved in: {plots_dir}")


if __name__ == "__main__":
    main()
