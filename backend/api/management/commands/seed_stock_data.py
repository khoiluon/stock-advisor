# backend/api/management/commands/seed_stock_data.py

import time
from datetime import datetime, timedelta
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import Stock, StockData
from vnstock import Listing, Quote

# --- CẤU HÌNH TỐI ƯU ---
BATCH_SIZE = 20000  # Tăng để nhanh hơn (Django bulk_create handle tốt)
INITIAL_DELAY = 1.5  # Cân bằng: Giảm nhẹ vì test ok, tránh rate limit
DEFAULT_START_DATE = '2020-01-01'  # Đủ cho TA dài hạn (~5.5 năm, ~1250 trading days/mã)

# Retry
MAX_GENERAL_RETRIES = 3
MAX_RATE_LIMIT_RETRIES = 30
RETRY_DELAY = 5
RATE_LIMIT_BASE_WAIT = 30

# Chế độ
TEST_MODE = False  # Set True nếu test 50 mã
RESUME_FROM_TICKER = None  # Set 'AAA' nếu resume

class Command(BaseCommand):
    help = 'Seed stocks & OHLCV data from 2020 (optimized for vnstock==3.2.6, full TA ready).'

    def add_arguments(self, parser):
        parser.add_argument('--clean', action='store_true', help='Clean old data before seeding.')
        parser.add_argument('--start-date', type=str, default=DEFAULT_START_DATE,
                            help='Start date (default: 2020-01-01).')
        parser.add_argument('--verify', action='store_true', help='Only verify existing data (no seeding).')

    @transaction.atomic
    def handle(self, *args, **options):
        start_date = options['start_date']
        verify_only = options['verify']
        self.stdout.write(self.style.SUCCESS(f"=== Seed/Verify từ {start_date} (vnstock==3.2.6, lần chạy cuối) ==="))

        if options['clean'] and not verify_only:
            self.stdout.write(self.style.WARNING("Xóa dữ liệu cũ..."))
            StockData.objects.all().delete()
            Stock.objects.all().delete()

        if verify_only:
            self._verify_data()
            return

        # --- GIAI ĐOẠN 1: METADATA (giữ nguyên, ổn định) ---
        self.stdout.write(self.style.NOTICE("\n[Giai đoạn 1/2] Lấy metadata..."))
        try:
            listing_client = Listing()
            df_full_list = listing_client.symbols_by_exchange()
            df_industries = listing_client.symbols_by_industries()

            industry_col = next((col for col in ['icb_name4', 'icb_name3', 'icb_name2'] if col in df_industries.columns), None)
            if industry_col:
                df_industries_subset = df_industries[['symbol', industry_col]].rename(columns={industry_col: 'industry'})
                df_companies = pd.merge(df_full_list, df_industries_subset, on='symbol', how='left')
                df_companies['industry'] = df_companies['industry'].fillna('N/A')
            else:
                df_companies = df_full_list.copy()
                df_companies['industry'] = 'N/A'

            self.stdout.write(self.style.SUCCESS(f"  -> Metadata cho {len(df_companies)} công ty."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  -> Lỗi metadata: {e}"))
            import traceback
            traceback.print_exc()
            return

        df_companies.dropna(subset=['symbol'], inplace=True)

        exchange_mapping = {'HOSE': 'HOSE', 'HNX': 'HNX', 'UPCOM': 'UPCOM'}
        stocks_to_create = [
            Stock(
                ticker=row['symbol'],
                company_name=row['organ_name'] if pd.notna(row['organ_name']) else row['symbol'],
                exchange=exchange_mapping.get(row['exchange'], 'OTHER'),
                industry=row['industry']
            )
            for index, row in df_companies.iterrows()
        ]

        Stock.objects.bulk_create(stocks_to_create, ignore_conflicts=True)
        all_stocks_map = {stock.ticker: stock for stock in Stock.objects.all()}
        tickers_in_db = list(all_stocks_map.keys())

        # Lọc mã hợp lệ (3-5 alpha, bỏ chứng quyền/trái phiếu)
        original_count = len(tickers_in_db)
        tickers_in_db = [ticker for ticker in tickers_in_db if 3 <= len(ticker) <= 5 and ticker.isalpha()]
        skipped_count = original_count - len(tickers_in_db)
        self.stdout.write(self.style.SUCCESS(f"  -> Lọc: {len(tickers_in_db)} mã hợp lệ, bỏ {skipped_count} mã."))

        if TEST_MODE:
            tickers_in_db = tickers_in_db[:50]
            self.stdout.write(self.style.WARNING(f"  -> TEST MODE: Chỉ {len(tickers_in_db)} mã."))

        if RESUME_FROM_TICKER:
            try:
                start_index = tickers_in_db.index(RESUME_FROM_TICKER)
                tickers_in_db = tickers_in_db[start_index:]
                self.stdout.write(self.style.WARNING(f"  -> Resume từ {RESUME_FROM_TICKER}: {len(tickers_in_db)} mã."))
            except ValueError:
                self.stdout.write(self.style.ERROR(f"  -> Không tìm thấy {RESUME_FROM_TICKER}."))
                return

        # --- GIAI ĐOẠN 2: SEED DATA (tối ưu date handling từ test) ---
        self.stdout.write(self.style.NOTICE(f"\n[Giai đoạn 2/2] Lấy OHLCV từ {start_date}..."))
        stock_data_to_create = []
        today_str = datetime.now().strftime('%Y-%m-%d')  # 2025-09-09

        success_count = 0
        error_count = 0
        low_data_count = 0
        start_time = datetime.now()

        i = 0
        while i < len(tickers_in_db):
            ticker = tickers_in_db[i]
            general_retry_count = 0
            rate_limit_retry_count = 0
            ticker_processed = False

            while (general_retry_count < MAX_GENERAL_RETRIES or rate_limit_retry_count < MAX_RATE_LIMIT_RETRIES) and not ticker_processed:
                try:
                    self.stdout.write(f"  -> {i + 1}/{len(tickers_in_db)}: {ticker} (G{general_retry_count}, RL{rate_limit_retry_count})")

                    quote_client = Quote(symbol=ticker)
                    df_history = quote_client.history(start=start_date, end=today_str, interval='1D')

                    if df_history is None or df_history.empty:
                        self.stdout.write(self.style.WARNING(f"    -> Không data cho {ticker} (mã mới?)."))
                        error_count += 1
                        ticker_processed = True
                        continue

                    # Date handling: Ưu tiên cột 'time' (như test)
                    if 'time' in df_history.columns:
                        df_history['time'] = pd.to_datetime(df_history['time'], format='%Y-%m-%d', errors='coerce')
                        date_source = 'time'
                    else:
                        # Fallback index (hiếm, nhưng an toàn)
                        df_history.index = pd.to_datetime(df_history.index, errors='coerce')
                        date_source = 'index'

                    required_columns = ['open', 'high', 'low', 'close', 'volume']
                    if not all(col in df_history.columns for col in required_columns):
                        raise ValueError(f"Thiếu cột OHLCV")

                    df_history.dropna(subset=required_columns + (['time'] if date_source == 'time' else []), inplace=True)
                    if df_history.empty:
                        raise ValueError("Data rỗng sau dropna")

                    stock_instance = all_stocks_map.get(ticker)
                    if not stock_instance:
                        ticker_processed = True
                        continue

                    rows_added = 0
                    min_date = None
                    max_date = None
                    dates_set = set()  # Tránh duplicate date

                    for idx, row in df_history.iterrows():
                        try:
                            if date_source == 'time':
                                index_date = row['time']
                            else:
                                index_date = idx

                            if pd.isna(index_date):
                                continue

                            date_obj = index_date.date()
                            if date_obj in dates_set:
                                continue  # Skip duplicate (nếu có)
                            dates_set.add(date_obj)

                            if min_date is None or date_obj < min_date:
                                min_date = date_obj
                            if max_date is None or date_obj > max_date:
                                max_date = date_obj

                            stock_data_to_create.append(
                                StockData(
                                    stock=stock_instance,
                                    date=date_obj,
                                    open=float(row['open']),
                                    high=float(row['high']),
                                    low=float(row['low']),
                                    close=float(row['close']),
                                    volume=int(row['volume'])
                                )
                            )
                            rows_added += 1
                        except (ValueError, TypeError, KeyError):
                            continue  # Skip row lỗi

                    if rows_added == 0:
                        raise ValueError("Không thêm row nào")

                    if rows_added < 200:  # Warning nếu ít (mã listing muộn)
                        low_data_count += 1
                        self.stdout.write(self.style.WARNING(f"    -> Data ít: {rows_added} rows cho {ticker}."))

                    self.stdout.write(f"    -> Thêm {rows_added} rows ({date_source}) cho {ticker} (từ {min_date} đến {max_date}).")

                    if len(stock_data_to_create) >= BATCH_SIZE:
                        self.stdout.write(f"    -> Lưu batch {len(stock_data_to_create)}...")
                        StockData.objects.bulk_create(stock_data_to_create, ignore_conflicts=True)
                        stock_data_to_create = []

                    success_count += 1
                    ticker_processed = True

                except Exception as e:
                    error_msg = str(e).lower()
                    is_rate_limit = any(phrase in error_msg for phrase in ["rate limit", "quá nhiều", "429", "throttled"])

                    if is_rate_limit:
                        rate_limit_retry_count += 1
                        wait_time = min(RATE_LIMIT_BASE_WAIT * (2 ** (rate_limit_retry_count - 1)), 300)
                        self.stdout.write(self.style.WARNING(f"⚠️ Rate limit {ticker}. Chờ {wait_time}s (lần {rate_limit_retry_count})."))
                        time.sleep(wait_time)
                        if rate_limit_retry_count >= MAX_RATE_LIMIT_RETRIES:
                            self.stdout.write(self.style.ERROR(f"    -> Bỏ {ticker} sau max RL."))
                            error_count += 1
                            ticker_processed = True
                    else:
                        general_retry_count += 1
                        if general_retry_count < MAX_GENERAL_RETRIES:
                            self.stdout.write(self.style.WARNING(f"    -> Lỗi tạm {ticker}: {str(e)[:50]}... Retry {RETRY_DELAY}s."))
                            time.sleep(RETRY_DELAY)
                        else:
                            self.stdout.write(self.style.ERROR(f"    -> Lỗi cố định {ticker}: {e}"))
                            error_count += 1
                            ticker_processed = True

            time.sleep(INITIAL_DELAY)
            i += 1

            # Progress (cải thiện ETA)
            elapsed = (datetime.now() - start_time).total_seconds()
            processed = i
            avg_time = elapsed / processed if processed > 0 else 0
            remaining = (len(tickers_in_db) - processed) * avg_time
            eta = datetime.now() + timedelta(seconds=remaining)
            self.stdout.write(self.style.NOTICE(
                f"    -> {processed}/{len(tickers_in_db)} | Success: {success_count} | Errors: {error_count} | Low: {low_data_count} | ETA: {remaining/60:.1f} min (~{eta.strftime('%H:%M')})"
            ))

        if stock_data_to_create:
            self.stdout.write(self.style.SUCCESS(f"    -> Lưu batch cuối {len(stock_data_to_create)}..."))
            StockData.objects.bulk_create(stock_data_to_create, ignore_conflicts=True)

        # Verify tổng quát & ví dụ
        self._verify_data()
        total_records = StockData.objects.count()
        total_time = (datetime.now() - start_time).total_seconds()
        self.stdout.write(self.style.SUCCESS(f"\n=== HOÀN TẤT LẦN CUỐI! ==="))
        self.stdout.write(self.style.SUCCESS(f"Thống kê: {success_count} success, {error_count} errors ({error_count/len(tickers_in_db)*100:.1f}%), {low_data_count} low data."))
        self.stdout.write(self.style.SUCCESS(f"Tổng records: {total_records} (~{total_records/success_count:.0f} rows/ticker trung bình)."))
        self.stdout.write(self.style.SUCCESS(f"Thời gian: {total_time/60:.1f} phút. Data sẵn sàng cho TA!"))

    def _verify_data(self):
        """Verify DB: Tổng records, ví dụ 5 ticker đầu với date range."""
        self.stdout.write(self.style.NOTICE("\n--- VERIFY DB ---"))
        total_records = StockData.objects.count()
        self.stdout.write(self.style.SUCCESS(f"Tổng records: {total_records}"))

        # Lấy 5 ticker đầu (alphabetical)
        top_stocks = Stock.objects.order_by('ticker')[:5]
        for stock in top_stocks:
            data_qs = StockData.objects.filter(stock=stock).order_by('date')
            if data_qs.exists():
                oldest = data_qs.first()
                latest = data_qs.last()
                count = data_qs.count()
                self.stdout.write(self.style.SUCCESS(f"{stock.ticker}: {count} rows, từ {oldest.date} đến {latest.date}"))
            else:
                self.stdout.write(self.style.WARNING(f"{stock.ticker}: Không có data!"))