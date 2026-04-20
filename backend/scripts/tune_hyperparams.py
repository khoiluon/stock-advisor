"""
Optuna Hyperparameter Tuning — Standalone script, KHÔNG cần Django.

Usage (từ thư mục backend/):
    python scripts/tune_hyperparams.py                    # 50 trials, both algos
    python scripts/tune_hyperparams.py --n-trials 100     # 100 trials
    python scripts/tune_hyperparams.py --algo lightgbm    # chỉ tune LightGBM
    python scripts/tune_hyperparams.py --timeout 3600     # max 1 giờ
    python scripts/tune_hyperparams.py --retrain-only      # skip tuning, retrain với results có sẵn

Steps:
1. Load features.parquet
2. Split train (2021-2024) / test (2025+)
3. Optuna: tune LightGBM + XGBoost trên subset D_0 × 3-fold expanding CV
4. Save best params → data/models/optuna_results.joblib
5. Retrain full ensemble (20 models) với best params → version v2
6. Evaluate v2 vs v1 trên holdout test set

Cần chạy build_features.py trước.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main():
    parser = argparse.ArgumentParser(description="Optuna Hyperparameter Tuning")
    parser.add_argument("--n-trials", type=int, default=50, help="Số trials mỗi algorithm (default: 50)")
    parser.add_argument("--timeout", type=int, default=None, help="Max seconds (default: no limit)")
    parser.add_argument("--algo", choices=["lightgbm", "xgboost", "both"], default="both", help="Algorithm to tune")
    parser.add_argument("--version", default="v2", help="Version string cho retrained models (default: v2)")
    parser.add_argument("--retrain-only", action="store_true", help="Skip tuning, chỉ retrain với results có sẵn")
    parser.add_argument("--no-retrain", action="store_true", help="Chỉ tune, không retrain")
    args = parser.parse_args()

    from ml.tuning import run_optuna_tuning, retrain_with_best_params

    if not args.retrain_only:
        # Step 1: Run Optuna tuning
        results = run_optuna_tuning(
            n_trials=args.n_trials,
            timeout=args.timeout,
            algo=args.algo,
        )

        # Print comparison
        print("\n" + "=" * 60)
        print("TUNING RESULTS SUMMARY")
        print("=" * 60)
        for alg, r in results.items():
            print(f"\n{alg.upper()}:")
            print(f"  Best Precision(UP): {r['best_value']:.4f}")
            print(f"  Best Params:")
            for k, v in r['best_params'].items():
                print(f"    {k}: {v}")
    else:
        results = None

    if not args.no_retrain:
        # Step 2: Retrain with best params
        print("\n" + "=" * 60)
        print(f"RETRAIN ENSEMBLE WITH BEST PARAMS → {args.version}")
        print("=" * 60)
        retrain_with_best_params(
            optuna_results=results if results else None,
            version=args.version,
        )

    print("\nDone!")


if __name__ == "__main__":
    main()
