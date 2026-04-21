"""
run_ml_predictions — Pipeline ML hàng ngày: export → features → predict → save DB.

Thay thế run_daily_prediction. Lưu kết quả vào:
  - MLPrediction: tất cả predictions (UP/DOWN/SIDEWAY)
  - AnomalyAlert: mã có dấu hiệu bất thường
  - MarketState: trạng thái thị trường ngày mới nhất
  - PotentialStock: backward compat (chỉ UP >= 60%) cho frontend screener

Usage:
    python manage.py run_ml_predictions              # full pipeline
    python manage.py run_ml_predictions --dry-run    # predict, không save DB
    python manage.py run_ml_predictions --skip-export --skip-features  # dùng data có sẵn
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
    help = 'Pipeline ML: export → features → predict → save MLPrediction + AnomalyAlert + MarketState'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Chỉ predict và in kết quả, không lưu DB',
        )
        parser.add_argument(
            '--skip-export', action='store_true',
            help='Bỏ qua bước export (dùng parquet có sẵn)',
        )
        parser.add_argument(
            '--skip-features', action='store_true',
            help='Bỏ qua bước compute features (dùng features parquet có sẵn)',
        )
        parser.add_argument(
            '--skip-anomaly', action='store_true',
            help='Bỏ qua anomaly detection',
        )
        parser.add_argument(
            '--skip-market-state', action='store_true',
            help='Bỏ qua market state computation',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        skip_export = options['skip_export']
        skip_features = options['skip_features']
        skip_anomaly = options['skip_anomaly']
        skip_market_state = options['skip_market_state']

        self.stdout.write(self.style.NOTICE("=" * 60))
        self.stdout.write("ML PREDICTIONS PIPELINE (Phase 5)")
        self.stdout.write(f"Time: {timezone.now()}")
        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN MODE]"))
        self.stdout.write(self.style.NOTICE("=" * 60))

        # ── Step 1: Export MLStockData → Parquet ──
        if not skip_export:
            self.stdout.write("\n[1/6] Exporting MLStockData → Parquet...")
            try:
                call_command("export_ml_data")
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Export failed: {e}"))
                return
        else:
            self.stdout.write("\n[1/6] Skipped export (--skip-export)")

        if not RAW_DATA_PATH.exists():
            self.stderr.write(self.style.ERROR(f"File not found: {RAW_DATA_PATH}"))
            return

        # ── Step 2: Compute Features ──
        if not skip_features:
            self.stdout.write("\n[2/6] Computing features (~50 indicators per stock)...")
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
            self.stdout.write("\n[2/6] Skipped features (--skip-features)")

        if not FEATURES_PATH.exists():
            self.stderr.write(self.style.ERROR(f"File not found: {FEATURES_PATH}"))
            return

        df_features = pd.read_parquet(FEATURES_PATH)

        # ── Step 3: Run Prediction ──
        self.stdout.write("\n[3/6] Running ML ensemble prediction...")
        try:
            predictions = predict_latest(df_features)
            self.stdout.write(f"  Predictions: {len(predictions)} stocks")
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Prediction failed: {e}"))
            return

        if predictions.empty:
            self.stdout.write(self.style.WARNING("  No predictions generated."))
            return

        # ── Step 4: Save to MLPrediction + PotentialStock ──
        self.stdout.write("\n[4/6] Saving predictions to database...")
        if not dry_run:
            try:
                saved_ml, saved_ps = self._save_predictions(predictions)
                self.stdout.write(self.style.SUCCESS(
                    f"  MLPrediction: {saved_ml} saved | PotentialStock: {saved_ps} saved (UP≥60%)"
                ))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Save predictions failed: {e}"))
        else:
            self.stdout.write(self.style.WARNING("  [DRY RUN] Skipping DB save"))

        self._print_prediction_summary(predictions)

        # ── Step 5: Anomaly Detection ──
        if not skip_anomaly:
            self.stdout.write("\n[5/6] Running anomaly detection...")
            try:
                anomaly_results = self._run_anomaly_detection(df_features)
                if anomaly_results is not None and not anomaly_results.empty:
                    anomalies = anomaly_results[anomaly_results['is_anomaly']]
                    self.stdout.write(f"  Detected {len(anomalies)} anomalies out of {len(anomaly_results)} stocks")
                    if not dry_run:
                        saved_a = self._save_anomalies(anomalies)
                        self.stdout.write(self.style.SUCCESS(f"  AnomalyAlert: {saved_a} saved"))
                    else:
                        self.stdout.write(self.style.WARNING("  [DRY RUN] Skipping anomaly save"))
                    self._print_anomaly_summary(anomalies)
                else:
                    self.stdout.write(self.style.WARNING("  No anomaly results generated."))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Anomaly detection failed: {e}"))
        else:
            self.stdout.write("\n[5/6] Skipped anomaly detection (--skip-anomaly)")

        # ── Step 6: Market State ──
        if not skip_market_state:
            self.stdout.write("\n[6/6] Computing market state...")
            try:
                market_state = self._run_market_state(df_features)
                if market_state is not None and not market_state.empty:
                    latest = market_state.iloc[-1]
                    self.stdout.write(
                        f"  Latest: {latest['state']} (confidence: {latest['confidence']}%, "
                        f"breadth: {latest['breadth_pct']:.1%})"
                    )
                    if not dry_run:
                        saved_ms = self._save_market_state(market_state)
                        self.stdout.write(self.style.SUCCESS(f"  MarketState: {saved_ms} saved/updated"))
                    else:
                        self.stdout.write(self.style.WARNING("  [DRY RUN] Skipping market state save"))
                else:
                    self.stdout.write(self.style.WARNING("  No market state generated."))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Market state failed: {e}"))
        else:
            self.stdout.write("\n[6/6] Skipped market state (--skip-market-state)")

        self.stdout.write(self.style.SUCCESS("\nPipeline hoàn thành!"))

    # ──────────────────────────────────────────────────────────
    # Prediction save
    # ──────────────────────────────────────────────────────────

    def _get_adj_factors(self):
        """Pre-fetch adj_factor = adj_close/close cho tất cả stocks (1 SQL query)."""
        from django.db import connection
        adj_factors = {}
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
                    adj_factors[stock_id] = float(adj_close) / float(close)
        return adj_factors

    def _save_predictions(self, predictions: pd.DataFrame):
        """Lưu predictions vào MLPrediction (tất cả) + PotentialStock (UP≥60% + thanh khoản đủ).

        Convert adjusted → raw price trước khi lưu.
        PotentialStock chỉ lưu stocks có ADTV hiện tại ≥ MIN_ADTV.
        """
        from api.models import MLPrediction, MLStock, PotentialStock, Stock
        from ml.config import MIN_ADTV

        today = timezone.now().date()
        adj_factors = self._get_adj_factors()
        current_adtv = self._get_current_adtv()

        # Xoá PotentialStock cũ cho hôm nay trước khi ghi mới
        # (tránh dữ liệu stale từ lần chạy trước với model version khác)
        deleted_count, _ = PotentialStock.objects.filter(analysis_date=today).delete()
        if deleted_count:
            self.stdout.write(f"  Cleaned {deleted_count} old PotentialStock records for {today}")

        saved_ml = 0
        saved_ps = 0
        skipped_liquidity = 0

        for _, row in predictions.iterrows():
            ticker = row['stock_id']

            # MLPrediction → FK to MLStock
            try:
                ml_stock = MLStock.objects.get(ticker=ticker)
            except MLStock.DoesNotExist:
                continue

            trend = row['trend_class']
            confidence = int(row['confidence_score'])
            adj_target = float(row['target_price'])
            adj_stop = float(row['stop_loss'])
            proba = row['trend_probability']

            # Convert adjusted → raw price
            adj_factor = adj_factors.get(ticker, 1.0)
            if adj_factor > 0:
                raw_target = adj_target / adj_factor
                raw_stop = adj_stop / adj_factor
            else:
                raw_target = adj_target
                raw_stop = adj_stop

            # Save to MLPrediction (ALL predictions)
            MLPrediction.objects.update_or_create(
                stock=ml_stock,
                prediction_date=today,
                defaults={
                    'trend_class': trend,
                    'trend_probability': proba,
                    'target_price': round(raw_target, 2),
                    'stop_loss': round(raw_stop, 2),
                    'confidence_score': confidence,
                }
            )
            saved_ml += 1

            # Backward compat: save UP≥50% to PotentialStock (with liquidity filter)
            if trend == 'UP' and confidence >= 50:
                # Liquidity gate: skip stocks with low current ADTV
                adtv = current_adtv.get(ticker, 0)
                if adtv < MIN_ADTV:
                    skipped_liquidity += 1
                    continue

                try:
                    stock = Stock.objects.get(ticker=ticker)
                except Stock.DoesNotExist:
                    continue

                key_reasons = (
                    f"ML Prediction: {trend} ({confidence}% confidence). "
                    f"UP: {proba['UP']:.1%}, DOWN: {proba['DOWN']:.1%}, SIDEWAY: {proba['SIDEWAY']:.1%}"
                )
                # current_price = adj_close converted to raw
                adj_current = float(row.get('adj_close', 0)) if 'adj_close' in row.index else 0
                raw_current = adj_current / adj_factor if adj_factor > 0 else adj_current

                PotentialStock.objects.update_or_create(
                    stock=stock,
                    analysis_date=today,
                    defaults={
                        'current_price': round(raw_current, 2),
                        'target_price': round(raw_target, 2),
                        'stop_loss': round(raw_stop, 2),
                        'key_reasons': key_reasons,
                        'confidence': confidence,
                        'timeframe': 'ML',
                    }
                )
                saved_ps += 1

        if skipped_liquidity:
            self.stdout.write(
                f"  Liquidity filter: skipped {skipped_liquidity} UP stocks "
                f"(ADTV < {MIN_ADTV/1e6:.0f}M VND)"
            )

        return saved_ml, saved_ps

    def _get_current_adtv(self):
        """Pre-fetch ADTV_20 hiện tại = AVG(close × volume) 20 ngày gần nhất per stock."""
        from django.db import connection
        adtv = {}
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT d.stock_id AS ticker, AVG(d.close * d.volume) AS adtv_20
                FROM api_mlstockdata d
                INNER JOIN (
                    SELECT stock_id, MAX(date) AS max_date
                    FROM api_mlstockdata
                    GROUP BY stock_id
                ) latest ON d.stock_id = latest.stock_id
                WHERE d.date > DATE_SUB(latest.max_date, INTERVAL 30 DAY)
                GROUP BY d.stock_id
            """)
            for ticker, avg_tv in cursor.fetchall():
                if avg_tv is not None:
                    adtv[ticker] = float(avg_tv)
        return adtv

    # ──────────────────────────────────────────────────────────
    # Anomaly Detection
    # ──────────────────────────────────────────────────────────

    def _run_anomaly_detection(self, df_features: pd.DataFrame) -> pd.DataFrame:
        """Load anomaly detector và predict cho ngày mới nhất."""
        from ml.anomaly import AnomalyDetector
        detector = AnomalyDetector.load()
        return detector.predict_latest(df_features)

    def _save_anomalies(self, anomalies: pd.DataFrame) -> int:
        """Lưu anomaly alerts vào AnomalyAlert."""
        from api.models import AnomalyAlert, MLStock

        now = timezone.now()
        saved = 0

        for _, row in anomalies.iterrows():
            ticker = row['stock_id']
            try:
                ml_stock = MLStock.objects.get(ticker=ticker)
            except MLStock.DoesNotExist:
                continue

            AnomalyAlert.objects.create(
                stock=ml_stock,
                detected_at=now,
                anomaly_type=row['anomaly_type'],
                anomaly_score=float(row['anomaly_score']),
                details={
                    'date': str(row['date']),
                }
            )
            saved += 1

        return saved

    # ──────────────────────────────────────────────────────────
    # Market State
    # ──────────────────────────────────────────────────────────

    def _run_market_state(self, df_features: pd.DataFrame) -> pd.DataFrame:
        """Compute market state series từ features."""
        from ml.market_state import get_market_state_series
        return get_market_state_series(df_features)

    def _save_market_state(self, market_state: pd.DataFrame) -> int:
        """Lưu market state mới nhất (hoặc batch) vào MarketState table."""
        from api.models import MarketState as MarketStateModel

        saved = 0
        # Chỉ lưu ngày mới nhất (daily pipeline)
        latest = market_state.iloc[-1]

        MarketStateModel.objects.update_or_create(
            date=latest['date'],
            defaults={
                'state': latest['state'],
                'confidence': int(latest['confidence']),
                'details': {
                    'breadth_pct': float(latest['breadth_pct']),
                }
            }
        )
        saved += 1

        return saved

    # ──────────────────────────────────────────────────────────
    # Summary
    # ──────────────────────────────────────────────────────────

    def _print_prediction_summary(self, predictions: pd.DataFrame):
        """In summary predictions."""
        self.stdout.write("\n--- Prediction Summary ---")
        for trend in ['UP', 'DOWN', 'SIDEWAY']:
            subset = predictions[predictions['trend_class'] == trend]
            if not subset.empty:
                avg_conf = subset['confidence_score'].mean()
                self.stdout.write(f"  {trend}: {len(subset)} stocks (avg confidence: {avg_conf:.0f}%)")

        # Top 10 UP signals
        up = predictions[predictions['trend_class'] == 'UP'].sort_values('confidence_score', ascending=False)
        if not up.empty:
            self.stdout.write("\n  Top 10 UP signals:")
            for _, row in up.head(10).iterrows():
                self.stdout.write(
                    f"    {row['stock_id']:>6s}  conf={row['confidence_score']:.0f}%  "
                    f"target={row['target_price']:.0f}  stop={row['stop_loss']:.0f}"
                )

    def _print_anomaly_summary(self, anomalies: pd.DataFrame):
        """In summary anomalies."""
        if anomalies.empty:
            return
        self.stdout.write("\n--- Anomaly Summary ---")
        type_counts = anomalies['anomaly_type'].value_counts()
        for atype, count in type_counts.items():
            self.stdout.write(f"  {atype}: {count}")
        # Top 5 most anomalous
        top = anomalies.sort_values('anomaly_score').head(5)
        self.stdout.write("  Top 5 most anomalous:")
        for _, row in top.iterrows():
            self.stdout.write(
                f"    {row['stock_id']:>6s}  score={row['anomaly_score']:.3f}  type={row['anomaly_type']}"
            )
