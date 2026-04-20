"""
export_ml_data_v2 — Export dữ liệu từ StockData (thay vì MLStockData) → Parquet cho ML pipeline.

Đây là phiên bản mới đọc từ bảng StockData + Stock duy nhất,
thay vì MLStockData + MLStock (bảng duplicate cũ).

Filter: stock_type='S', is_active=True, có adj_close

So sánh:
  export_ml_data    → đọc từ MLStockData (bảng cũ, duplicate)
  export_ml_data_v2 → đọc từ StockData   (bảng chính, single source of truth)

Usage:
    python manage.py export_ml_data_v2
    python manage.py export_ml_data_v2 --start-date 2022-01-01
    python manage.py export_ml_data_v2 --compare    # so sánh output với export_ml_data cũ
"""
import pandas as pd
import numpy as np
from django.core.management.base import BaseCommand

from api.models import Stock, StockData
from ml.config import DATA_START_DATE, RAW_DATA_PATH, STOCK_META_PATH


class Command(BaseCommand):
    help = 'Export adjusted OHLCV từ StockData (single source) sang Parquet cho ML pipeline'

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-date', type=str, default=DATA_START_DATE,
            help=f'Start date (default: {DATA_START_DATE})',
        )
        parser.add_argument(
            '--stock-type', type=str, default='S',
            help='Stock type to filter (default: S)',
        )
        parser.add_argument(
            '--output', type=str, default=None,
            help='Custom output path. Default: data/raw/ohlcv_adjusted.parquet',
        )
        parser.add_argument(
            '--compare', action='store_true',
            help='So sánh output với file parquet hiện tại (không ghi đè)',
        )

    def handle(self, *args, **options):
        start_date = options['start_date']
        stock_type = options['stock_type']
        output_path = options['output']
        compare_mode = options['compare']

        self.stdout.write(f"Export v2: stock_type='{stock_type}', date >= {start_date}")
        self.stdout.write(f"Source: StockData + Stock (single source of truth)")

        # 1. Query data from StockData (NOT MLStockData)
        qs = StockData.objects.filter(
            date__gte=start_date,
            stock__is_active=True,
        ).select_related('stock')

        if stock_type:
            qs = qs.filter(stock__stock_type=stock_type)

        # Chỉ lấy rows có adj_close (streaming data không có → loại)
        qs = qs.exclude(adj_close__isnull=True)

        qs = qs.order_by('stock__ticker', 'date')

        self.stdout.write("Querying database...")
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
            self.stderr.write(self.style.ERROR("Không có data! Kiểm tra stock_type, date, adj_close."))
            return

        df = pd.DataFrame(records)
        df.rename(columns={
            'stock__ticker': 'stock_id',
            'stock__exchange': 'exchange',
            'stock__industry': 'industry',
        }, inplace=True)

        self.stdout.write(f"Raw data: {len(df):,} rows, {df['stock_id'].nunique()} stocks")

        # 2. Convert numeric types
        for col in ['open', 'high', 'low', 'close', 'adj_close']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0).astype(np.int64)

        # Drop rows có giá trị null sau convert
        before = len(df)
        df = df.dropna(subset=['adj_close', 'close', 'open', 'high', 'low'])
        dropped = before - len(df)
        if dropped > 0:
            self.stdout.write(self.style.WARNING(f"Dropped {dropped:,} rows với giá trị null"))

        # 3. Tính adj_factor và adjusted OHLCV
        df['adj_factor'] = np.where(df['close'] != 0, df['adj_close'] / df['close'], 1.0)
        df['adj_open'] = df['open'] * df['adj_factor']
        df['adj_high'] = df['high'] * df['adj_factor']
        df['adj_low'] = df['low'] * df['adj_factor']
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

        # 6. Compare mode
        if compare_mode:
            self._compare_with_existing(df)
            return

        # 7. Export to Parquet
        from pathlib import Path
        out = Path(output_path) if output_path else RAW_DATA_PATH
        out.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out, index=False, engine='pyarrow')

        self.stdout.write(self.style.SUCCESS(
            f"\nExport v2 thành công: {out}\n"
            f"  Rows: {len(df):,}\n"
            f"  Stocks: {df['stock_id'].nunique()}\n"
            f"  Date range: {df['date'].min()} → {df['date'].max()}"
        ))

        # 8. Export stock metadata
        meta = df[['stock_id', 'exchange', 'industry']].drop_duplicates('stock_id')
        STOCK_META_PATH.parent.mkdir(parents=True, exist_ok=True)
        meta.to_parquet(STOCK_META_PATH, index=False, engine='pyarrow')
        self.stdout.write(f"  Stock metadata: {STOCK_META_PATH} ({len(meta)} stocks)")

    def _compare_with_existing(self, df_new):
        """So sánh output mới (từ StockData) với parquet hiện tại (từ MLStockData)."""
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("SO SÁNH: export_ml_data_v2 (StockData) vs export_ml_data (MLStockData)")
        self.stdout.write("=" * 60)

        if not RAW_DATA_PATH.exists():
            self.stdout.write(self.style.WARNING(f"File cũ không tồn tại: {RAW_DATA_PATH}"))
            self.stdout.write(f"\nDữ liệu mới (v2):")
            self.stdout.write(f"  Rows: {len(df_new):,}")
            self.stdout.write(f"  Stocks: {df_new['stock_id'].nunique()}")
            self.stdout.write(f"  Date range: {df_new['date'].min()} → {df_new['date'].max()}")
            return

        df_old = pd.read_parquet(RAW_DATA_PATH)

        self.stdout.write(f"\n{'':20s} {'OLD (MLStockData)':>20s}  {'NEW (StockData)':>20s}")
        self.stdout.write(f"{'Rows':20s} {len(df_old):>20,}  {len(df_new):>20,}")
        self.stdout.write(f"{'Stocks':20s} {df_old['stock_id'].nunique():>20,}  {df_new['stock_id'].nunique():>20,}")
        self.stdout.write(f"{'Date min':20s} {str(df_old['date'].min()):>20s}  {str(df_new['date'].min()):>20s}")
        self.stdout.write(f"{'Date max':20s} {str(df_old['date'].max()):>20s}  {str(df_new['date'].max()):>20s}")

        # Stock overlap
        old_stocks = set(df_old['stock_id'].unique())
        new_stocks = set(df_new['stock_id'].unique())
        common = old_stocks & new_stocks
        only_old = old_stocks - new_stocks
        only_new = new_stocks - old_stocks

        self.stdout.write(f"\nStock overlap:")
        self.stdout.write(f"  Chung: {len(common)}")
        self.stdout.write(f"  Chỉ OLD: {len(only_old)}")
        if only_old and len(only_old) <= 20:
            self.stdout.write(f"    {sorted(only_old)}")
        self.stdout.write(f"  Chỉ NEW: {len(only_new)}")
        if only_new and len(only_new) <= 20:
            self.stdout.write(f"    {sorted(only_new)}")

        # Data diff cho common stocks
        if common:
            df_old_c = df_old[df_old['stock_id'].isin(common)].copy()
            df_new_c = df_new[df_new['stock_id'].isin(common)].copy()

            # Convert dates to comparable format
            df_old_c['date'] = pd.to_datetime(df_old_c['date'])
            df_new_c['date'] = pd.to_datetime(df_new_c['date'])

            merged = df_old_c.merge(
                df_new_c,
                on=['stock_id', 'date'],
                suffixes=('_old', '_new'),
                how='outer',
                indicator=True,
            )

            self.stdout.write(f"\nRow overlap (common stocks):")
            self.stdout.write(f"  Both: {(merged['_merge'] == 'both').sum():,}")
            self.stdout.write(f"  Only OLD: {(merged['_merge'] == 'left_only').sum():,}")
            self.stdout.write(f"  Only NEW: {(merged['_merge'] == 'right_only').sum():,}")

            # Check adj_close differences
            both = merged[merged['_merge'] == 'both']
            if len(both) > 0:
                diff = (both['adj_close_old'] - both['adj_close_new']).abs()
                self.stdout.write(f"\n  adj_close diff (rows chung):")
                self.stdout.write(f"    Mean diff: {diff.mean():.6f}")
                self.stdout.write(f"    Max diff: {diff.max():.6f}")
                self.stdout.write(f"    Rows with diff > 0.01: {(diff > 0.01).sum():,}")

        self.stdout.write(f"\nKết luận: {'✅ Dữ liệu tương đương' if len(only_old) == 0 and len(only_new) == 0 else '⚠️ Có sự khác biệt — kiểm tra chi tiết'}")
