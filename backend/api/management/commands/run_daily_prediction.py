"""
run_daily_prediction — Pipeline ML hàng ngày: export → features → predict → save DB.

Chạy sau khi sync_ohlc_history hoàn thành (thường 18:30 T2-T6).
Kết quả lưu vào PotentialStock để hiển thị trên frontend sáng hôm sau.

Usage:
    python manage.py run_daily_prediction             # full pipeline
    python manage.py run_daily_prediction --dry-run   # chỉ predict, không save DB
"""
import pandas as pd
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone

from ml.config import RAW_DATA_PATH, FEATURES_PATH
from ml.features import compute_features
from ml.labeling import create_labeled_dataset
from ml.prediction import predict_latest


class Command(BaseCommand):
    help = 'Pipeline ML hàng ngày: export data → compute features → predict → save kết quả'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Chỉ predict và in kết quả, không lưu DB',
        )
        parser.add_argument(
            '--skip-export', action='store_true',
            help='Bỏ qua bước export (dùng data/raw/ohlcv_adjusted.parquet có sẵn)',
        )
        parser.add_argument(
            '--skip-features', action='store_true',
            help='Bỏ qua bước compute features (dùng data/features/features.parquet có sẵn)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        skip_export = options['skip_export']
        skip_features = options['skip_features']

        self.stdout.write(self.style.NOTICE("=" * 60))
        self.stdout.write("DAILY ML PREDICTION PIPELINE")
        self.stdout.write(f"Time: {timezone.now()}")
        self.stdout.write(self.style.NOTICE("=" * 60))

        # ── Step 1: Export MLStockData → Parquet ──
        if not skip_export:
            self.stdout.write("\n[1/4] Exporting MLStockData → Parquet...")
            try:
                call_command("export_ml_data")
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Export failed: {e}"))
                return
        else:
            self.stdout.write("\n[1/4] Skipped export (--skip-export)")

        if not RAW_DATA_PATH.exists():
            self.stderr.write(self.style.ERROR(f"File not found: {RAW_DATA_PATH}"))
            return

        # ── Step 2: Compute Features ──
        if not skip_features:
            self.stdout.write("\n[2/4] Computing features (~50 indicators per stock)...")
            try:
                df = pd.read_parquet(RAW_DATA_PATH)
                self.stdout.write(f"  Raw data: {len(df):,} rows, {df['stock_id'].nunique()} stocks")
                df_feat = compute_features(df)
                self.stdout.write(f"  Features computed: {df_feat.shape}")

                df_labeled = create_labeled_dataset(df_feat)
                FEATURES_PATH.parent.mkdir(parents=True, exist_ok=True)
                df_labeled.to_parquet(FEATURES_PATH, index=False)
                self.stdout.write(f"  Saved → {FEATURES_PATH}")
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Feature computation failed: {e}"))
                return
        else:
            self.stdout.write("\n[2/4] Skipped features (--skip-features)")

        if not FEATURES_PATH.exists():
            self.stderr.write(self.style.ERROR(f"File not found: {FEATURES_PATH}"))
            return

        # ── Step 3: Run Prediction ──
        self.stdout.write("\n[3/4] Running ML ensemble prediction...")
        try:
            df_features = pd.read_parquet(FEATURES_PATH)
            predictions = predict_latest(df_features)
            self.stdout.write(f"  Predictions: {len(predictions)} stocks")
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Prediction failed: {e}"))
            return

        if predictions.empty:
            self.stdout.write(self.style.WARNING("  No predictions generated."))
            return

        # ── Step 4: Save to PotentialStock ──
        self.stdout.write("\n[4/4] Saving predictions to database...")
        if dry_run:
            self.stdout.write(self.style.WARNING("  [DRY RUN] Skipping DB save"))
            self._print_summary(predictions)
            return

        try:
            saved = self._save_predictions(predictions)
            self.stdout.write(self.style.SUCCESS(f"  Saved {saved} predictions to PotentialStock"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Save failed: {e}"))
            return

        self._print_summary(predictions)
        self.stdout.write(self.style.SUCCESS("\nPipeline hoàn thành!"))

    def _save_predictions(self, predictions: pd.DataFrame) -> int:
        """Lưu predictions vào PotentialStock (upsert by ticker + date).

        ML pipeline tính target_price/stop_loss trên giá ADJUSTED.
        Cần convert về giá GỐC (raw) trước khi lưu DB vì người dùng
        nhìn giá gốc trên sàn chứng khoán.

        Công thức: raw_price = adjusted_price / adj_factor
        Trong đó: adj_factor = adj_close / close (từ MLStockData ngày mới nhất)
        """
        from api.models import PotentialStock, Stock, MLStockData

        today = timezone.now().date()
        saved = 0

        # Pre-fetch adj_factor cho tất cả stocks (1 raw SQL query)
        from django.db import connection
        latest_ml_data = {}
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT d.stock_id, d.close, d.adj_close
                FROM api_mlstockdata d
                INNER JOIN (
                    SELECT stock_id, MAX(date) AS max_date
                    FROM api_mlstockdata
                    GROUP BY stock_id
                ) latest ON d.stock_id = latest.stock_id AND d.date = latest.max_date
            """)
            for stock_id, close, adj_close in cursor.fetchall():
                if adj_close and close and float(close) > 0:
                    latest_ml_data[stock_id] = float(adj_close) / float(close)

        for _, row in predictions.iterrows():
            ticker = row['stock_id']
            try:
                stock = Stock.objects.get(ticker=ticker)
            except Stock.DoesNotExist:
                continue

            trend = row['trend_class']
            confidence = int(row['confidence_score'])
            adj_target = float(row['target_price'])
            adj_stop = float(row['stop_loss'])
            proba = row['trend_probability']

            # Convert adjusted → raw price
            adj_factor = latest_ml_data.get(ticker, 1.0)
            if adj_factor > 0:
                raw_target = adj_target / adj_factor
                raw_stop = adj_stop / adj_factor
            else:
                raw_target = adj_target
                raw_stop = adj_stop

            key_reasons = (
                f"ML Prediction: {trend} ({confidence}% confidence). "
                f"UP: {proba['UP']:.1%}, DOWN: {proba['DOWN']:.1%}, SIDEWAY: {proba['SIDEWAY']:.1%}"
            )

            # Chỉ lưu mã có xu hướng UP với confidence >= 60%
            if trend != 'UP' or confidence < 60:
                continue

            PotentialStock.objects.update_or_create(
                stock=stock,
                date=today,
                defaults={
                    'target_price': round(raw_target, 2),
                    'stop_loss': round(raw_stop, 2),
                    'key_reasons': key_reasons,
                    'confidence_score': confidence,
                }
            )
            saved += 1

        return saved

    def _print_summary(self, predictions: pd.DataFrame):
        """In summary predictions."""
        self.stdout.write("\n--- Prediction Summary ---")
        for trend in ['UP', 'DOWN', 'SIDEWAY']:
            subset = predictions[predictions['trend_class'] == trend]
            if not subset.empty:
                avg_conf = subset['confidence_score'].mean()
                self.stdout.write(f"  {trend}: {len(subset)} stocks (avg confidence: {avg_conf:.0f}%)")

        # Top 10 UP signals
        up_stocks = predictions[predictions['trend_class'] == 'UP'].sort_values(
            'confidence_score', ascending=False
        ).head(10)
        if not up_stocks.empty:
            self.stdout.write("\n  Top 10 UP signals:")
            for _, row in up_stocks.iterrows():
                self.stdout.write(
                    f"    {row['stock_id']:>6s}: {row['confidence_score']}% "
                    f"(target: {row['target_price']:,.0f}, SL: {row['stop_loss']:,.0f})"
                )
