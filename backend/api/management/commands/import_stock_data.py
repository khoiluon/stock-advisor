# backend/api/management/commands/seed_stock_data.py

import time
from datetime import datetime, timedelta
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import Stock, StockData
from vnstock import Listing, Quote

# --- CẤU HÌNH ---
BATCH_SIZE = 10000
INITIAL_DELAY = 2.0
START_DATE = '2000-01-01'

MAX_GENERAL_RETRIES = 3
MAX_RATE_LIMIT_RETRIES = 30
RETRY_DELAY = 5
RATE_LIMIT_BASE_WAIT = 30

TEST_MODE = False
RESUME_FROM_TICKER = None


class Command(BaseCommand):
    help = 'Seeds the database with all stocks and their full historical data using vnstock (Fixed date issue).'

    @transaction.atomic
    def add_arguments(self, parser):
        parser.add_argument('--clean', action='store_true', help='Clean old data before seeding.')

    def handle(self, *args, **options):
        if options['clean']:
            self.stdout.write(self.style.WARNING("Xóa dữ liệu cũ..."))
            StockData.objects.all().delete()
            Stock.objects.all().delete()

        self.stdout.write(
            self.style.SUCCESS("=== Bắt đầu quy trình nạp dữ liệu từ vnstock (Phiên bản sửa lỗi date) ==="))

        # --- GIAI ĐOẠN 1: LẤY METADATA CỔ PHIẾU ---
        self.stdout.write(self.style.NOTICE("\n[Giai đoạn 1/2] Lấy danh sách, tên công ty, sàn và ngành..."))

        try:
            listing_client = Listing()
            self.stdout.write("    -> Lấy danh sách theo sàn...")
            df_full_list = listing_client.symbols_by_exchange()

            self.stdout.write("    -> Lấy danh sách theo ngành...")
            df_industries = listing_client.symbols_by_industries()

            self.stdout.write("    -> Trộn dữ liệu sàn và ngành...")
            industry_col = next(
                (col for col in ['icb_name4', 'icb_name3', 'icb_name2'] if col in df_industries.columns), None)

            if industry_col:
                df_industries_subset = df_industries[['symbol', industry_col]].rename(
                    columns={industry_col: 'industry'})
                df_companies = pd.merge(df_full_list, df_industries_subset, on='symbol', how='left')
                df_companies['industry'] = df_companies['industry'].fillna('N/A')
            else:
                self.stdout.write(self.style.WARNING("    -> Không tìm thấy cột industry. Gán là 'N/A'."))
                df_companies = df_full_list.copy()
                df_companies['industry'] = 'N/A'

            self.stdout.write(self.style.SUCCESS(f"  -> Lấy thành công metadata cho {len(df_companies)} công ty."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  -> Lỗi khi lấy danh sách cổ phiếu: {e}"))
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

        self.stdout.write(self.style.SUCCESS(f"  -> Đang lưu {len(stocks_to_create)} cổ phiếu vào database..."))
        Stock.objects.bulk_create(stocks_to_create, ignore_conflicts=True)

        all_stocks_map = {stock.ticker: stock for stock in Stock.objects.all()}
        tickers_in_db = list(all_stocks_map.keys())

        original_count = len(tickers_in_db)
        tickers_in_db = [
            ticker for ticker in tickers_in_db
            if 3 <= len(ticker) <= 5 and ticker.isalpha() and not any(c.isdigit() for c in ticker)
        ]
        skipped_count = original_count - len(tickers_in_db)

        self.stdout.write(self.style.SUCCESS(
            f"  -> Lọc thành công: Giữ {len(tickers_in_db)} mã cổ phiếu hợp lệ, bỏ qua {skipped_count} mã (chứng quyền/trái phiếu/không hợp lệ)."))

        if TEST_MODE:
            tickers_in_db = tickers_in_db[:50]
            self.stdout.write(
                self.style.WARNING(f"  -> CHẾ ĐỘ TEST: Chỉ xử lý {len(tickers_in_db)} mã đầu tiên sau lọc."))

        if RESUME_FROM_TICKER:
            try:
                start_index = tickers_in_db.index(RESUME_FROM_TICKER)
                tickers_in_db = tickers_in_db[start_index:]
                self.stdout.write(
                    self.style.WARNING(f"  -> TIẾP TỤC từ mã {RESUME_FROM_TICKER} (còn lại {len(tickers_in_db)} mã)."))
            except ValueError:
                self.stdout.write(self.style.ERROR(f"  -> Không tìm thấy mã {RESUME_FROM_TICKER}."))
                return

        # --- GIAI ĐOẠN 2: LẤY DỮ LIỆU LỊCH SỬ (SỬA LỖI DATE) ---
        self.stdout.write(self.style.NOTICE("\n[Giai đoạn 2/2] Lấy dữ liệu giá lịch sử..."))
        stock_data_to_create = []
        today_str = datetime.now().strftime('%Y-%m-%d')

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

            while (
                    general_retry_count < MAX_GENERAL_RETRIES or rate_limit_retry_count < MAX_RATE_LIMIT_RETRIES) and not ticker_processed:
                try:
                    self.stdout.write(
                        f"  -> Đang xử lý mã {i + 1}/{len(tickers_in_db)}: {ticker} (Retry: G{general_retry_count}/{MAX_GENERAL_RETRIES}, RL{rate_limit_retry_count}/{MAX_RATE_LIMIT_RETRIES})")

                    quote_client = Quote(symbol=ticker)
                    df_history = quote_client.history(start=START_DATE, end=today_str, interval='1D')

                    if df_history is None or df_history.empty:
                        self.stdout.write(self.style.WARNING(f"    -> Mã {ticker} không có dữ liệu. Bỏ qua."))
                        error_count += 1
                        ticker_processed = True
                        continue

                    # SỬA LỖI DATE: Ưu tiên cột 'time' nếu có (thông dụng trong vnstock)
                    date_col = 'time' if 'time' in df_history.columns else None
                    if date_col:
                        df_history[date_col] = pd.to_datetime(df_history[date_col], format='%Y-%m-%d', errors='coerce')
                        self.stdout.write(f"    -> Sử dụng cột '{date_col}' cho date.")
                    else:
                        # Fallback: Convert index nếu là datetime-like
                        if not isinstance(df_history.index, pd.DatetimeIndex):
                            df_history.index = pd.to_datetime(df_history.index, format='%Y-%m-%d', errors='coerce')
                        self.stdout.write(f"    -> Sử dụng index cho date.")

                    required_columns = ['open', 'high', 'low', 'close', 'volume']
                    if not all(col in df_history.columns for col in required_columns):
                        self.stdout.write(self.style.WARNING(f"    -> Thiếu cột dữ liệu cho {ticker}. Bỏ qua."))
                        error_count += 1
                        ticker_processed = True
                        continue

                    df_history.dropna(subset=required_columns + ([date_col] if date_col else []), inplace=True)
                    if df_history.empty:
                        self.stdout.write(self.style.WARNING(f"    -> Dữ liệu {ticker} rỗng sau lọc. Bỏ qua."))
                        error_count += 1
                        ticker_processed = True
                        continue

                    stock_instance = all_stocks_map.get(ticker)
                    if not stock_instance:
                        ticker_processed = True
                        continue

                    rows_added = 0
                    for _, row in df_history.iterrows():
                        try:
                            if date_col:
                                index_date = row[date_col]
                            else:
                                index_date = df_history.index[rows_added]  # Hoặc row.name nếu multiindex

                            if pd.isna(index_date):
                                self.stdout.write(self.style.WARNING(f"    -> Skip row với date NaT cho {ticker}."))
                                continue

                            date_obj = index_date.date()
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
                        except (ValueError, TypeError) as row_err:
                            self.stdout.write(self.style.WARNING(f"    -> Skip row lỗi date cho {ticker}: {row_err}"))
                            continue  # Skip row này, không bỏ ticker

                    if rows_added == 0:
                        self.stdout.write(self.style.WARNING(f"    -> Không thêm được row nào cho {ticker}. Bỏ qua."))
                        error_count += 1
                        ticker_processed = True
                        continue

                    if rows_added < 100:  # Warning nếu data ít (mã mới hoặc lỗi)
                        low_data_count += 1
                        self.stdout.write(self.style.WARNING(f"    -> Data ít cho {ticker}: chỉ {rows_added} rows."))

                    self.stdout.write(f"    -> Thêm {rows_added} rows cho {ticker}.")

                    if len(stock_data_to_create) >= BATCH_SIZE:
                        self.stdout.write(f"    -> Lưu batch {len(stock_data_to_create)} bản ghi...")
                        StockData.objects.bulk_create(stock_data_to_create, ignore_conflicts=True)
                        stock_data_to_create = []

                    success_count += 1
                    ticker_processed = True

                except Exception as e:
                    error_msg = str(e)
                    is_rate_limit = "Rate limit exceeded" in error_msg or "quá nhiều request" in error_msg or "429" in error_msg

                    if is_rate_limit:
                        rate_limit_retry_count += 1
                        wait_time = min(RATE_LIMIT_BASE_WAIT * (2 ** (rate_limit_retry_count - 1)), 300)  # Cap 5 phút
                        self.stdout.write(self.style.WARNING(
                            f"⚠️ Rate limit {ticker}. Chờ {wait_time}s (lần {rate_limit_retry_count})."))
                        time.sleep(wait_time)
                        if rate_limit_retry_count >= MAX_RATE_LIMIT_RETRIES:
                            self.stdout.write(self.style.ERROR(f"    -> Bỏ qua {ticker} sau max rate limit retries."))
                            error_count += 1
                            ticker_processed = True
                    else:
                        general_retry_count += 1
                        if general_retry_count < MAX_GENERAL_RETRIES:
                            self.stdout.write(self.style.WARNING(
                                f"    -> Lỗi tạm {ticker}. Retry sau {RETRY_DELAY}s (lần {general_retry_count})."))
                            time.sleep(RETRY_DELAY)
                        else:
                            self.stdout.write(self.style.ERROR(f"    -> Lỗi cố định {ticker}: {error_msg}"))
                            error_count += 1
                            ticker_processed = True

            if ticker_processed:
                time.sleep(INITIAL_DELAY)
                i += 1

            elapsed = (datetime.now() - start_time).total_seconds()
            processed = i
            avg_time_per_ticker = elapsed / processed if processed > 0 else 0
            remaining_tickers = len(tickers_in_db) - processed
            remaining_seconds = remaining_tickers * avg_time_per_ticker
            eta = datetime.now() + timedelta(seconds=remaining_seconds)
            self.stdout.write(self.style.NOTICE(
                f"    -> Tiến độ: {processed}/{len(tickers_in_db)} | Success: {success_count} | Errors: {error_count} | Low data: {low_data_count} | ETA: {remaining_seconds / 60:.1f} phút ({eta.strftime('%H:%M:%S')})"
            ))

        # Lưu batch cuối
        if stock_data_to_create:
            self.stdout.write(self.style.SUCCESS(f"    -> Lưu {len(stock_data_to_create)} bản ghi cuối..."))
            StockData.objects.bulk_create(stock_data_to_create, ignore_conflicts=True)

        # Verify tổng data
        total_records = StockData.objects.count()
        self.stdout.write(self.style.SUCCESS(f"\n=== HOÀN TẤT! ==="))
        self.stdout.write(self.style.SUCCESS(
            f"Thống kê: {success_count} ticker thành công, {error_count} lỗi, {low_data_count} ticker data ít."))
        self.stdout.write(self.style.SUCCESS(f"Tổng records trong DB: {total_records} (nên ~3-5M cho lịch sử đầy đủ)."))
        total_time = (datetime.now() - start_time).total_seconds()
        self.stdout.write(self.style.SUCCESS(f"Thời gian chạy: {total_time / 60:.1f} phút."))