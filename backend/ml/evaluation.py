"""
ML Evaluation — Metrics, confusion matrix, feature importance plots.

Không import Django, không import ORM.
"""
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional

from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    log_loss,
    precision_score,
)

from .config import LABEL_MAP_INV, MODELS_DIR


# ------------------------------------------------------------------
# Core metrics
# ------------------------------------------------------------------
def evaluate_classification(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: Optional[np.ndarray] = None,
    label_names: List[str] = None,
) -> Dict:
    """
    Tính đầy đủ classification metrics.

    Returns
    -------
    dict với keys: report_str, precision_up, logloss (nếu có proba), confusion_matrix
    """
    if label_names is None:
        label_names = [LABEL_MAP_INV[i] for i in sorted(LABEL_MAP_INV)]

    report = classification_report(
        y_true, y_pred, target_names=label_names, zero_division=0
    )

    # Precision(UP) — metric chính (class 0 = UP)
    precision_up = precision_score(
        y_true, y_pred, labels=[0], average="macro", zero_division=0
    )

    cm = confusion_matrix(y_true, y_pred)

    result = {
        "report_str": report,
        "precision_up": float(precision_up),
        "confusion_matrix": cm,
    }

    if y_proba is not None:
        try:
            result["logloss"] = float(log_loss(y_true, y_proba))
        except Exception:
            result["logloss"] = None

    return result


def evaluate_ensemble(
    models: List[Dict],
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> Dict:
    """
    Evaluate ensemble: average proba → final prediction → metrics.
    Cũng so sánh từng single model vs ensemble.
    """
    from .training import TrendModelTrainer

    # Ensemble prediction
    result = TrendModelTrainer.predict_ensemble(X_test, models)
    proba = result["proba"]
    pred = result["pred_class"]

    print("\n=== Ensemble Evaluation ===")
    metrics = evaluate_classification(y_test.values, pred, proba)
    print(metrics["report_str"])
    print(f"Precision(UP): {metrics['precision_up']:.4f}")
    if metrics.get("logloss"):
        print(f"Log-loss: {metrics['logloss']:.4f}")

    metrics["ensemble_pred"] = pred
    metrics["ensemble_proba"] = proba

    return metrics


# ------------------------------------------------------------------
# Plots (matplotlib — optional, graceful fallback nếu không có display)
# ------------------------------------------------------------------
def plot_confusion_matrix(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    save_path: Optional[Path] = None,
    label_names: List[str] = None,
) -> None:
    """Vẽ confusion matrix, save PNG nếu save_path được cung cấp."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import seaborn as sns
    except ImportError:
        print("matplotlib/seaborn không có — bỏ qua plot.")
        return

    if label_names is None:
        label_names = [LABEL_MAP_INV[i] for i in sorted(LABEL_MAP_INV)]

    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=label_names,
        yticklabels=label_names,
        ax=ax,
    )
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title("Confusion Matrix")
    plt.tight_layout()

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150)
        print(f"Saved confusion matrix → {save_path}")
    else:
        plt.show()
    plt.close(fig)


def plot_feature_importance(
    model,
    feature_names: List[str],
    top_n: int = 20,
    save_path: Optional[Path] = None,
) -> None:
    """Vẽ feature importance (LightGBM built-in), save PNG nếu save_path được cung cấp."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib không có — bỏ qua plot.")
        return

    importances = getattr(model, "feature_importances_", None)
    if importances is None:
        print("Model không có feature_importances_ attribute.")
        return

    series = pd.Series(importances, index=feature_names)
    top = series.nlargest(top_n)

    fig, ax = plt.subplots(figsize=(8, top_n * 0.35 + 1))
    top[::-1].plot(kind="barh", ax=ax)
    ax.set_title(f"Top {top_n} Feature Importance")
    ax.set_xlabel("Importance")
    plt.tight_layout()

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150)
        print(f"Saved feature importance → {save_path}")
    else:
        plt.show()
    plt.close(fig)
