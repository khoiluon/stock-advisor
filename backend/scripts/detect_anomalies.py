"""
Detect Anomalies — Standalone script, KHÔNG cần Django.

Usage (từ thư mục backend/):
    python scripts/detect_anomalies.py          # Fit + predict latest
    python scripts/detect_anomalies.py --fit    # Chỉ fit & save models
    python scripts/detect_anomalies.py --predict # Chỉ predict (cần đã fit)

Steps:
1. Load features từ data/features/features.parquet
2. Fit IsolationForest per-stock (hoặc load saved models)
3. Predict anomalies cho ngày mới nhất mỗi stock
4. In danh sách các mã bất thường

Cần chạy build_features.py trước.
"""
import argparse
import sys
from pathlib import Path

# Đảm bảo import được từ backend/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.anomaly import AnomalyDetector
from ml.config import FEATURES_PATH, MODELS_DIR
from ml.utils import load_features


def main() -> None:
    parser = argparse.ArgumentParser(description="Anomaly Detection Pipeline")
    parser.add_argument(
        "--fit", action="store_true",
        help="Chỉ fit models & save (không predict)",
    )
    parser.add_argument(
        "--predict", action="store_true",
        help="Chỉ predict từ saved models (không fit lại)",
    )
    args = parser.parse_args()

    # Default: fit + predict
    do_fit = not args.predict  # fit trừ khi --predict only
    do_predict = not args.fit  # predict trừ khi --fit only

    print("=" * 60)
    print("STEP 1: Load features")
    print("=" * 60)
    df = load_features(FEATURES_PATH)

    detector: AnomalyDetector

    if do_fit:
        print("\n" + "=" * 60)
        print("STEP 2: Fit AnomalyDetector (IsolationForest per-stock)")
        print("=" * 60)
        detector = AnomalyDetector()
        detector.fit(df)

        save_path = detector.save()
        print(f"Models saved → {save_path}")
    else:
        print("\n" + "=" * 60)
        print("STEP 2: Load saved AnomalyDetector")
        print("=" * 60)
        detector = AnomalyDetector.load()

    if do_predict:
        print("\n" + "=" * 60)
        print("STEP 3: Predict anomalies (latest date per stock)")
        print("=" * 60)
        results = detector.predict_latest(df)

        anomalies = results[
            (results['is_anomaly']) &
            (results['anomaly_score'] < -0.10)
        ].sort_values('anomaly_score')

        print(f"\n--- Anomaly Summary ---")
        print(f"Total stocks analyzed: {len(results)}")
        print(f"Anomalies detected: {len(anomalies)}")
        print(f"Anomaly rate: {len(anomalies) / len(results) * 100:.1f}%")

        if len(anomalies) > 0:
            print(f"\nAnomaly type distribution:")
            print(anomalies['anomaly_type'].value_counts().to_string())

            print(f"\nTop 20 most anomalous stocks:")
            display_cols = ['stock_id', 'date', 'anomaly_score', 'anomaly_type']
            print(anomalies[display_cols].head(20).to_string(index=False))
        else:
            print("\nKhông phát hiện anomaly nào trong ngày mới nhất.")


if __name__ == "__main__":
    main()
