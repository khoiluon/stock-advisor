"""
Backfill ML predictions cho tất cả ngày lịch sử → frontend xem được.

Usage:
    python manage.py backfill_predictions
    python manage.py backfill_predictions --start-date 2025-01-01
    python manage.py backfill_predictions --sample          # 20 stocks test
    python manage.py backfill_predictions --dry-run          # không lưu DB
"""
from datetime import date

import numpy as np
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction

from api.models import MLStock, Stock, MLPrediction, MLModel, PotentialStock
from ml.config import FEATURES_PATH, MODELS_DIR, MODEL_VERSION, MIN_ADTV
from ml.prediction import predict_all
from ml.training import load_ensemble
from ml.utils import load_features


class Command(BaseCommand):
    help = 'Backfill ML predictions cho tất cả ngày lịch sử từ features.parquet.'

    def add_arguments(self, parser):
        parser.add_argument('--start-date', type=str, default='2025-01-01')
        parser.add_argument('--end-date', type=str, default=None)
        parser.add_argument('--sample', action='store_true',
                            help='Chỉ xử lý 20 stocks (test nhanh).')
        parser.add_argument('--dry-run', action='store_true',
                            help='Không ghi DB, chỉ in thống kê.')
        parser.add_argument('--skip-potential', action='store_true',
                            help='Chỉ lưu MLPrediction, bỏ qua PotentialStock.')
        parser.add_argument('--model-version', type=str, default=MODEL_VERSION)
        parser.add_argument('--batch-size', type=int, default=500,
                            help='Batch size cho bulk_create.')

    @transaction.atomic
    def handle(self, *args, **options):
        start_date = options['start_date']
        end_date = options['end_date']
        sample = options['sample']
        dry_run = options['dry_run']
        skip_potential = options['skip_potential']
        version = options['model_version']
        batch_size = options['batch_size']

        self.stdout.write(self.style.NOTICE("=" * 60))
        self.stdout.write("BACKFILL ML PREDICTIONS")
        self.stdout.write(f"Version: {version} | Range: {start_date} → {end_date or 'latest'}")
        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN — không ghi DB]"))
        self.stdout.write(self.style.NOTICE("=" * 60))

        # 1. Load features + models
        self.stdout.write("\n[1/5] Loading features...")
        df = load_features(FEATURES_PATH)
        df = df[df['date'] >= start_date]
        if end_date:
            df = df[df['date'] <= end_date]

        if sample:
            sample_stocks = (
                df['stock_id'].drop_duplicates()
                .sample(n=min(20, df['stock_id'].nunique()), random_state=42)
                .tolist()
            )
            df = df[df['stock_id'].isin(sample_stocks)]
            self.stdout.write(f"  Sample mode: {len(df):,} rows, {len(sample_stocks)} stocks")

        self.stdout.write(f"  Data: {len(df):,} rows, {df['stock_id'].nunique()} stocks")
        self.stdout.write(f"  Date range: {df['date'].min()} → {df['date'].max()}")

        # 2. Load models
        self.stdout.write(f"\n[2/5] Loading model ensemble (v={version})...")
        models = load_ensemble(MODELS_DIR, version=version)
        self.stdout.write(f"  Loaded {len(models)} models")

        # 3. Predict
        self.stdout.write("\n[3/5] Running predict_all()...")
        try:
            df_pred = predict_all(df, models=models, version=version)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"predict_all failed: {e}"))
            return

        self.stdout.write(f"  Predictions: {len(df_pred):,} rows")
        for trend in ['UP', 'DOWN', 'SIDEWAY']:
            n = int((df_pred['trend_class'] == trend).sum())
            self.stdout.write(f"    {trend}: {n:,}")

        if dry_run:
            self.stdout.write(self.style.SUCCESS("\n[DRY RUN] Done. No data written."))
            return

        # 4. Pre-load stock mappings
        self.stdout.write("\n[4/5] Loading stock mappings...")
        ml_stocks = {s.ticker: s for s in MLStock.objects.all()}
        stocks = {s.ticker: s for s in Stock.objects.all()}
        self.stdout.write(f"  MLStock: {len(ml_stocks)}, Stock: {len(stocks)}")

        # Try to get or create default MLModel record
        ml_model, _ = MLModel.objects.get_or_create(
            name='Trend Ensemble',
            model_type='trend',
            version=version,
            defaults={
                'file_path': str(MODELS_DIR),
                'trained_at': pd.Timestamp.now(tz='Asia/Ho_Chi_Minh'),
                'is_active': True,
            },
        )

        # 5. Save predictions
        self.stdout.write("\n[5/5] Saving to DB...")
        mlp_batch = []
        ps_batch = []
        saved_ml = 0
        saved_ps = 0
        skipped_ticker = 0

        for _, row in df_pred.iterrows():
            ticker = row['stock_id']
            pred_date = pd.Timestamp(row['date']).date()

            ml_stock = ml_stocks.get(ticker)
            if ml_stock is None:
                skipped_ticker += 1
                continue

            trend = row['trend_class']
            confidence = int(row['confidence_score'])
            proba = row['trend_probability']

            # MLPrediction
            mlp_batch.append(MLPrediction(
                stock=ml_stock,
                prediction_date=pred_date,
                model=ml_model,
                trend_class=trend,
                trend_probability=proba,
                target_price=round(float(row['target_price']), 2),
                stop_loss=round(float(row['stop_loss']), 2),
                confidence_score=confidence,
            ))

            if len(mlp_batch) >= batch_size:
                MLPrediction.objects.bulk_create(
                    mlp_batch, ignore_conflicts=True)
                saved_ml += len(mlp_batch)
                mlp_batch = []

            # PotentialStock — chỉ UP + confidence >= 50
            if not skip_potential and trend == 'UP' and confidence >= 50:
                stock = stocks.get(ticker)
                if stock is None:
                    continue

                adj_close = float(row.get('adj_close', 0))
                adj_factor = adj_close / float(adj_close) if adj_close > 0 else 1.0
                raw_target = float(row['target_price']) / adj_factor if adj_factor > 0 else float(row['target_price'])
                raw_stop = float(row['stop_loss']) / adj_factor if adj_factor > 0 else float(row['stop_loss'])

                key_reasons = row.get('key_reasons', '') or (
                    f"ML Prediction: {trend} ({confidence}% confidence). "
                    f"UP: {proba.get('UP', 0):.1%}, "
                    f"DOWN: {proba.get('DOWN', 0):.1%}, "
                    f"SIDEWAY: {proba.get('SIDEWAY', 0):.1%}"
                )

                ps_batch.append(PotentialStock(
                    stock=stock,
                    analysis_date=pred_date,
                    current_price=round(float(row.get('adj_close', 0)), 2),
                    target_price=round(raw_target, 2),
                    stop_loss=round(raw_stop, 2),
                    key_reasons=str(key_reasons),
                    confidence=confidence,
                    timeframe='ML',
                ))

                if len(ps_batch) >= batch_size:
                    PotentialStock.objects.bulk_create(
                        ps_batch, ignore_conflicts=True,
                    )
                    saved_ps += len(ps_batch)
                    ps_batch = []

        # Flush batches cuối
        if mlp_batch:
            MLPrediction.objects.bulk_create(
                mlp_batch, ignore_conflicts=True)
            saved_ml += len(mlp_batch)

        if ps_batch:
            PotentialStock.objects.bulk_create(ps_batch, ignore_conflicts=True)
            saved_ps += len(ps_batch)

        self.stdout.write(self.style.SUCCESS(
            f"\nDone!\n"
            f"  MLPrediction saved:   {saved_ml:,}\n"
            f"  PotentialStock saved: {saved_ps:,}\n"
            f"  Skipped (no MLStock): {skipped_ticker:,}"
        ))
