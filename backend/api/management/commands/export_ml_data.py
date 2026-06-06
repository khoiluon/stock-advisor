"""
Export dữ liệu từ MySQL → Parquet cho ML pipeline.

Quy trình:
1. Query StockData JOIN Stock (filter stock_type='S', date >= DATA_START_DATE)
2. Tính adj_factor = adj_close / close
3. Tính adjusted OHLCV: adj_open, adj_high, adj_low, adj_volume = volume / adj_factor
4. Export ra Parquet file

Usage:
    python manage.py export_ml_data
    python manage.py export_ml_data --start-date 2022-01-01
"""
import pandas as pd
import numpy as np
from django.core.management.base import BaseCommand
from django.db.models import F

from api.models import Stock, StockData
from ml.config import DATA_START_DATE, RAW_DATA_PATH, STOCK_META_PATH


class Command(BaseCommand):
    help = 'Export adjusted OHLCV data từ DB sang Parquet cho ML pipeline'

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-date',
            type=str,
            default=DATA_START_DATE,
            help=f'Start date for data export (default: {DATA_START_DATE})',
        )
        parser.add_argument(
            '--stock-type',
            type=str,
            default='S',
            help='Stock type to filter (default: S = cổ phiếu thường)',
        )

    def handle(self, *args, **options):
        start_date = options['start_date']
        stock_type = options['stock_type']

        self.stdout.write(f"Exporting data: stock_type='{stock_type}', date >= {start_date}")

        # 1. Query data
        qs = StockData.objects.filter(
            date__gte=start_date,
            stock__is_active=True,
        ).select_related('stock')

        if stock_type:
            qs = qs.filter(stock__stock_type=stock_type)

        qs = qs.order_by('stock__ticker', 'date')

        self.stdout.write(f"Querying database...")
        records = list(
            qs.values(
                'stock__ticker',
                'stock__exchange',
                'stock__industry',
                'date',
                'open', 'high', 'low', 'close',
                'volume',
                'adj_close',
            )
        )

        if not records:
            self.stderr.write(self.style.ERROR("Không có data! Kiểm tra stock_type và date."))
            return

        df = pd.DataFrame(records)
        df.rename(columns={'stock__ticker': 'stock_id', 'stock__exchange': 'exchange', 'stock__industry': 'industry'}, inplace=True)

        self.stdout.write(f"Raw data: {len(df):,} rows, {df['stock_id'].nunique()} stocks")

        # 2. Drop rows thiếu adj_close
        before = len(df)
        df = df.dropna(subset=['adj_close'])
        dropped = before - len(df)
        if dropped > 0:
            self.stdout.write(self.style.WARNING(f"Dropped {dropped:,} rows thiếu adj_close"))

        # Convert numeric types
        for col in ['open', 'high', 'low', 'close', 'adj_close']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0).astype(np.int64)

        # 3. Tính adj_factor và adjusted OHLCV
        # adj_factor = adj_close / close
        df['adj_factor'] = np.where(df['close'] != 0, df['adj_close'] / df['close'], 1.0)

        df['adj_open'] = df['open'] * df['adj_factor']
        df['adj_high'] = df['high'] * df['adj_factor']
        df['adj_low'] = df['low'] * df['adj_factor']
        # adj_volume = volume / adj_factor (DIVIDE, not multiply)
        df['adj_volume'] = np.where(
            df['adj_factor'] != 0,
            df['volume'] / df['adj_factor'],
            df['volume']
        ).astype(np.int64)

        # 4. Validation
        invalid_mask = (
            (df['adj_close'] <= 0)
            | (df['adj_open'] <= 0)
            | (df['adj_low'] > df['adj_high'])
        )
        invalid_count = invalid_mask.sum()
        if invalid_count > 0:
            self.stdout.write(self.style.WARNING(f"Dropping {invalid_count:,} invalid rows"))
            df = df[~invalid_mask]

        # 5. Select final columns
        export_cols = [
            'stock_id', 'date',
            'adj_open', 'adj_high', 'adj_low', 'adj_close', 'adj_volume',
            'exchange', 'industry',
        ]
        df = df[export_cols].reset_index(drop=True)

        # 6. Export to Parquet
        RAW_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(RAW_DATA_PATH, index=False, engine='pyarrow')

        self.stdout.write(self.style.SUCCESS(
            f"\nExport thành công: {RAW_DATA_PATH}\n"
            f"  Rows: {len(df):,}\n"
            f"  Stocks: {df['stock_id'].nunique()}\n"
            f"  Date range: {df['date'].min()} → {df['date'].max()}"
        ))

        # 7. Export stock metadata
        meta = df[['stock_id', 'exchange', 'industry']].drop_duplicates('stock_id')
        STOCK_META_PATH.parent.mkdir(parents=True, exist_ok=True)
        meta.to_parquet(STOCK_META_PATH, index=False, engine='pyarrow')
        self.stdout.write(f"  Stock metadata: {STOCK_META_PATH} ({len(meta)} stocks)")
