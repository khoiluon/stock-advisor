import time
from datetime import date as date_type, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Max

from ssi_fc_data.fc_md_client import MarketDataClient
from ssi_fc_data.model.model import daily_stock_price

from ssi_integration.ssi_config import get_ssi_config
from ssi_integration.services import _throttled_request, _response_ok
from api.models import Stock, MLStock, MLStockData

REQUEST_INTERVAL = 1.0
CHUNK_DAYS = 28  # SSI API giới hạn ~30 ngày/request


def _parse_stock_price_item(item, ticker):
    # Filter theo symbol — SSI API trả về data TOÀN BỘ market
    item_symbol = item.get('Symbol') or item.get('symbol') or ''
    if not item_symbol or item_symbol.upper() != ticker.upper():
        return None

    trading_date_str = item.get('TradingDate')
    if not trading_date_str:
        return None
    try:
        day, month, year = map(int, trading_date_str.split('/'))
        open_price = float(item.get('OpenPrice', 0))
        high_price = float(item.get('HighestPrice', 0))
        low_price = float(item.get('LowestPrice', 0))
        close_price = float(item.get('ClosePrice', 0))
        raw_volume = item.get('TotalMatchVol') or item.get('TotalTradedVol') or 0
        volume = int(raw_volume)
        raw_adj = item.get('ClosePriceAdjusted')
        adj_close = float(raw_adj) if raw_adj is not None else None

        if close_price <= 0 or open_price <= 0:
            return None
        if volume < 0:
            return None
        if low_price > high_price:
            return None

        return date_type(year, month, day), open_price, high_price, low_price, close_price, volume, adj_close
    except (ValueError, TypeError):
        return None


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--from-date', type=str, default=None,
            help='Fetch từ ngày này (YYYY-MM-DD). Mặc định: tự detect MAX(date)+1 per stock.',
        )
        parser.add_argument(
            '--to-date', type=str, default=None,
            help='Fetch đến ngày này (YYYY-MM-DD). Mặc định: hôm qua, hoặc hôm nay nếu --include-today.',
        )
        parser.add_argument(
            '--ticker', type=str, default=None,
            help='Chỉ cập nhật cho 1 mã cụ thể',
        )
        parser.add_argument(
            '--stock-type', type=str, default='S',
            help='Loại cổ phiếu cần sync (default: S)',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Chỉ thống kê, không ghi DB',
        )
        parser.add_argument(
            '--include-today', action='store_true',
            help='Bao gồm ngày hôm nay (mặc định chỉ đến hôm qua để tránh API treo khi data chưa sẵn sàng)',
        )

    def handle(self, *args, **options):
        from_date_str = options['from_date']
        to_date_str = options['to_date']
        ticker = options['ticker']
        stock_type = options['stock_type']
        dry_run = options['dry_run']
        include_today = options['include_today']

        today = timezone.now().date()
        # Mặc định sync đến hôm qua để tránh gọi ngày chưa có data.
        # Dùng --include-today hoặc --to-date để override.
        end_date = today if include_today else (today - timedelta(days=1))

        if to_date_str:
            end_date = date_type.fromisoformat(to_date_str)

        if end_date > today:
            self.stdout.write(self.style.WARNING(f"to-date {end_date} > today {today}, dùng today."))
            end_date = today

        # Parse --from-date nếu có
        forced_from_date = None
        if from_date_str:
            forced_from_date = date_type.fromisoformat(from_date_str)

        if forced_from_date and forced_from_date > end_date:
            self.stderr.write(self.style.ERROR(f"from-date {forced_from_date} > end-date {end_date}"))
            return

        # 1. Xác định danh sách stocks cần sync (từ bảng Stock, filter type)
        stock_qs = Stock.objects.filter(is_active=True)
        if stock_type:
            stock_qs = stock_qs.filter(stock_type=stock_type)
        if ticker:
            stock_qs = stock_qs.filter(ticker=ticker)

        stock_tickers = list(stock_qs.values_list('ticker', flat=True))
        self.stdout.write(f"Stocks cần sync: {len(stock_tickers)} (type={stock_type})")

        if not stock_tickers:
            self.stderr.write("Không có stock nào phù hợp.")
            return

        # 2. Lấy MAX(date) per stock trong MLStockData (1 query duy nhất)
        last_dates = dict(
            MLStockData.objects.filter(stock_id__in=stock_tickers)
            .values_list('stock_id')
            .annotate(last_date=Max('date'))
            .values_list('stock_id', 'last_date')
        )
        stocks_with_data = sum(1 for d in last_dates.values() if d is not None)
        stocks_no_data = len(stock_tickers) - stocks_with_data

        if forced_from_date:
            self.stdout.write(f"Mode: forced from {forced_from_date} → {end_date}")
        else:
            if last_dates:
                global_max = max((d for d in last_dates.values() if d), default=None)
                global_min = min((d for d in last_dates.values() if d), default=None)
                self.stdout.write(
                    f"Mode: incremental (per-stock MAX(date)+1 → {end_date})"
                    f"{'  (include-today)' if include_today else ''}\n"
                    f"  Stocks có data: {stocks_with_data} (last: {global_min} → {global_max})\n"
                    f"  Stocks chưa có data: {stocks_no_data}"
                )
            else:
                self.stdout.write(f"Mode: incremental (MLStockData trống, sẽ skip mã chưa có data)")

        # 3. Khởi tạo SSI client
        self.stdout.write("Đang khởi tạo SSI Client...")
        try:
            config = get_ssi_config()
            client = MarketDataClient(config)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Không thể khởi tạo SSI Client: {e}"))
            return

        # 4. Phân nhóm stocks theo from_date
        total_created = 0
        total_skipped = 0
        errors = []

        # Xác định from_date cho từng stock
        stock_tasks = {}  # ticker -> from_date
        for stk_ticker in stock_tickers:
            if forced_from_date:
                stk_from = forced_from_date
            else:
                stk_last = last_dates.get(stk_ticker)
                if stk_last is None:
                    total_skipped += 1
                    continue
                stk_from = stk_last + timedelta(days=1)
            if stk_from > end_date:
                total_skipped += 1
                continue
            stock_tasks[stk_ticker] = stk_from

        # Tìm from_date phổ biến nhất → batch fetch
        from_date_counts = {}
        for stk_from in stock_tasks.values():
            from_date_counts[stk_from] = from_date_counts.get(stk_from, 0) + 1

        BATCH_THRESHOLD = 20
        batch_from = None
        if from_date_counts:
            most_common = max(from_date_counts, key=from_date_counts.get)
            if from_date_counts[most_common] >= BATCH_THRESHOLD:
                batch_from = most_common

        # --- BATCH MODE: 1 API call cho tất cả stocks cùng from_date ---
        if batch_from is not None:
            batch_tickers = [t for t, f in stock_tasks.items() if f == batch_from]
            self.stdout.write(
                f"\n--- BATCH MODE: {len(batch_tickers)} tickers, "
                f"{batch_from} → {end_date} ---"
            )
            try:
                batch_cache = self._batch_fetch_date_range(
                    client, config, batch_from, end_date
                )
                batch_saved = 0
                for stk_ticker in batch_tickers:
                    ticker_data = batch_cache.get(stk_ticker, [])
                    if ticker_data and not dry_run:
                        created = self._save_ticker_data(stk_ticker, ticker_data, dry_run)
                        total_created += created
                        batch_saved += created
                    elif ticker_data and dry_run:
                        total_created += len(ticker_data)
                        batch_saved += len(ticker_data)
                    else:
                        total_skipped += 1
                self.stdout.write(f"  Batch saved: {batch_saved} rows for {len(batch_tickers)} tickers")
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"  Batch fetch failed: {e}"))
                errors.append(("BATCH", str(e)))
                # Fallback: đưa lại vào per-stock mode
                self.stdout.write("  Falling back to per-stock mode...")
                batch_from = None  # Reset để xử lý ở per-stock bên dưới

            # Xóa batch tickers khỏi stock_tasks (nếu batch thành công)
            if batch_from is not None:
                for t in batch_tickers:
                    stock_tasks.pop(t, None)

        # --- PER-STOCK MODE: cho stocks có from_date khác ---
        remaining = list(stock_tasks.items())
        if remaining:
            self.stdout.write(f"\n--- PER-STOCK MODE: {len(remaining)} tickers ---")
            for i, (stk_ticker, stk_from) in enumerate(remaining):
                if (i + 1) % 100 == 0 or i == 0:
                    self.stdout.write(f"\n--- [{i+1}/{len(remaining)}] ---")
                try:
                    created = self._sync_stock(
                        client, config, stk_ticker, stk_from, end_date, dry_run
                    )
                    total_created += created
                    if created == 0:
                        total_skipped += 1
                except Exception as e:
                    errors.append((stk_ticker, str(e)))
                    self.stderr.write(f"  ERROR {stk_ticker}: {e}")
                time.sleep(REQUEST_INTERVAL)

        # 5. Report
        self.stdout.write(self.style.SUCCESS(f"\n{'[DRY RUN] ' if dry_run else ''}Hoàn thành sync_ohlc_history!"))
        self.stdout.write(f"  Created new rows: {total_created}")
        self.stdout.write(f"  Skipped (up-to-date): {total_skipped}")
        if errors:
            self.stdout.write(self.style.WARNING(f"  Errors: {len(errors)}"))
            for t, e in errors[:10]:
                self.stdout.write(f"    {t}: {e}")

    def _batch_fetch_date_range(self, client, config, from_date, to_date):
        all_data = {}
        chunk_start = from_date
        chunk_num = 0

        while chunk_start <= to_date:
            chunk_end = min(chunk_start + timedelta(days=CHUNK_DAYS), to_date)
            chunk_num += 1

            t0 = time.time()
            req = daily_stock_price(
                symbol='',
                fromDate=chunk_start.strftime('%d/%m/%Y'),
                toDate=chunk_end.strftime('%d/%m/%Y'),
                pageIndex=1,
                pageSize=10000,
                market='',
            )
            response = _throttled_request(
                client.daily_stock_price, config, req,
                context=f"batch-chunk{chunk_num} {chunk_start}→{chunk_end}"
            )
            elapsed = time.time() - t0

            if _response_ok(response) and response.get('data'):
                data = response['data']
                for item in data:
                    sym = (item.get('Symbol') or '').upper()
                    if not sym:
                        continue
                    parsed = _parse_stock_price_item(item, sym)
                    if parsed:
                        all_data.setdefault(sym, []).append(parsed)
                self.stdout.write(
                    f"  Batch chunk {chunk_num} ({chunk_start} → {chunk_end}): "
                    f"{len(data)} rows → {len(all_data)} tickers ({elapsed:.1f}s)"
                )
            else:
                self.stdout.write(
                    f"  Batch chunk {chunk_num} ({chunk_start} → {chunk_end}): "
                    f"no data ({elapsed:.1f}s)"
                )

            chunk_start = chunk_end + timedelta(days=1)
            time.sleep(REQUEST_INTERVAL)

        return all_data

    def _save_ticker_data(self, ticker, data, dry_run):
        """Save parsed OHLCV data for a single ticker to MLStockData."""
        try:
            ml_stock = MLStock.objects.get(ticker=ticker)
        except MLStock.DoesNotExist:
            try:
                stock = Stock.objects.get(ticker=ticker)
                ml_stock = MLStock.objects.create(
                    ticker=stock.ticker,
                    company_name=stock.company_name,
                    exchange=stock.exchange,
                    industry=stock.industry,
                    stock_type=stock.stock_type,
                    is_active=stock.is_active,
                )
            except Stock.DoesNotExist:
                return 0

        # Deduplicate by date
        seen = set()
        unique = []
        for row in data:
            if row[0] not in seen:
                seen.add(row[0])
                unique.append(row)

        if not unique:
            return 0
        if dry_run:
            return len(unique)

        rows = [
            MLStockData(
                stock=ml_stock, date=td,
                open=op, high=hp, low=lp, close=cp,
                volume=vol, adj_close=adj,
            )
            for td, op, hp, lp, cp, vol, adj in unique
        ]
        MLStockData.objects.bulk_create(rows, ignore_conflicts=True)
        return len(rows)

    def _sync_stock(self, client, config, ticker, from_date, to_date, dry_run):
        # Đảm bảo MLStock record tồn tại
        try:
            ml_stock = MLStock.objects.get(ticker=ticker)
        except MLStock.DoesNotExist:
            try:
                stock = Stock.objects.get(ticker=ticker)
                ml_stock = MLStock.objects.create(
                    ticker=stock.ticker,
                    company_name=stock.company_name,
                    exchange=stock.exchange,
                    industry=stock.industry,
                    stock_type=stock.stock_type,
                    is_active=stock.is_active,
                )
            except Stock.DoesNotExist:
                return 0

        market = ml_stock.exchange or 'HOSE'

        total_created = 0
        chunk_start = from_date
        chunk_num = 0

        while chunk_start <= to_date:
            chunk_end = min(chunk_start + timedelta(days=CHUNK_DAYS), to_date)
            chunk_num += 1

            chunk_t0 = time.time()
            self.stdout.write(f"  {ticker}: chunk {chunk_num} ({chunk_start} → {chunk_end})...")
            self.stdout.flush()

            chunk_data = []
            page_index = 1
            page_size = 1000  # Lớn để giảm số API calls (SSI trả ALL stocks)
            consecutive_empty = 0  # Track pages không có data cho ticker

            while True:
                api_t0 = time.time()
                req = daily_stock_price(
                    symbol=ticker,
                    fromDate=chunk_start.strftime('%d/%m/%Y'),
                    toDate=chunk_end.strftime('%d/%m/%Y'),
                    pageIndex=page_index,
                    pageSize=page_size,
                    market=market,
                )
                response = _throttled_request(
                    client.daily_stock_price, config, req,
                    context=f"{ticker} {chunk_start}→{chunk_end} p{page_index}"
                )
                api_elapsed = time.time() - api_t0

                if not (_response_ok(response) and response.get('data')):
                    self.stdout.write(f"    p{page_index}: NO DATA (api={api_elapsed:.1f}s)")
                    break

                page_data = response['data']
                found_in_page = 0
                for item in page_data:
                    parsed = _parse_stock_price_item(item, ticker)
                    if parsed is not None:
                        chunk_data.append(parsed)
                        found_in_page += 1

                self.stdout.write(
                    f"    p{page_index}: {len(page_data)} rows total, "
                    f"{found_in_page} for {ticker}, "
                    f"cumul={len(chunk_data)}, api={api_elapsed:.1f}s"
                )

                if len(page_data) < page_size:
                    self.stdout.write(f"    → last page (len < page_size)")
                    break  # Trang cuối cùng

                # SSI trả nhiều hơn page_size → API dump toàn bộ, page 1 đã đủ
                if len(page_data) > page_size:
                    self.stdout.write(f"    → API returned {len(page_data)} > page_size {page_size}, all data in page 1")
                    break

                # SSI trả ALL stocks → nếu 2 trang liên tiếp không có
                # data cho ticker → đã quét đủ, stop
                if found_in_page == 0:
                    consecutive_empty += 1
                    if consecutive_empty >= 2:
                        self.stdout.write(f"    → 2 consecutive empty pages, stopping")
                        break
                else:
                    consecutive_empty = 0

                # Đã tìm đủ data (28 ngày max ~22 ngày giao dịch)
                if len(chunk_data) >= 25:
                    self.stdout.write(f"    → enough data ({len(chunk_data)} >= 25), stopping")
                    break

                page_index += 1
                time.sleep(REQUEST_INTERVAL)

            chunk_elapsed = time.time() - chunk_t0
            self.stdout.write(f"  {ticker}: chunk {chunk_num} done in {chunk_elapsed:.1f}s, {len(chunk_data)} records")

            # Save chunk ngay lập tức
            if chunk_data and not dry_run:
                # Deduplicate by date (SSI có thể trả duplicate records)
                seen_dates = set()
                unique_data = []
                for row in chunk_data:
                    if row[0] not in seen_dates:  # row[0] = date
                        seen_dates.add(row[0])
                        unique_data.append(row)

                new_rows = [
                    MLStockData(
                        stock=ml_stock, date=td,
                        open=op, high=hp, low=lp, close=cp,
                        volume=vol, adj_close=adj,
                    )
                    for td, op, hp, lp, cp, vol, adj in unique_data
                ]
                MLStockData.objects.bulk_create(new_rows, ignore_conflicts=True)
                total_created += len(new_rows)
                self.stdout.write(f" +{len(new_rows)} rows saved")
            elif chunk_data and dry_run:
                total_created += len(chunk_data)
                self.stdout.write(f" {len(chunk_data)} rows (dry-run)")
            else:
                self.stdout.write(f" 0 rows")

            chunk_start = chunk_end + timedelta(days=1)
            time.sleep(REQUEST_INTERVAL)

        return total_created
