"""
sync_ohlc_history — Đồng bộ OHLCV + adj_close vào MLStockData từ daily_stock_price API.

Ghi vào MLStockData (giá GỐC + adj_close) — KHÔNG phải StockData (giá đã adjusted cho biểu đồ).
Chỉ gọi API cho stock_type='S' (ML eligible, ~1,813 mã).

Chế độ INCREMENTAL mặc định:
  - Tự detect MAX(date) per stock trong MLStockData
  - Chỉ fetch từ MAX(date)+1 → hôm nay
  - VCB có data đến 2025-12-19 → chỉ fetch từ 2025-12-20

Usage:
    python manage.py sync_ohlc_history                        # incremental (tự detect)
    python manage.py sync_ohlc_history --from-date 2026-01-01 # từ ngày cụ thể
    python manage.py sync_ohlc_history --ticker VCB           # chỉ 1 mã
    python manage.py sync_ohlc_history --ticker VCB --from-date 2026-04-01
    python manage.py sync_ohlc_history --dry-run              # chỉ thống kê
"""
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
    """
    Parse một bản ghi từ daily_stock_price API (có ClosePriceAdjusted).
    Chỉ parse record khớp ticker (SSI API có thể trả về nhiều mã).
    Return: (date, open, high, low, close, volume, adj_close) hoặc None.
    """
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
    help = 'Đồng bộ OHLCV + adj_close vào MLStockData (incremental, chỉ stock_type=S)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--from-date', type=str, default=None,
            help='Fetch từ ngày này (YYYY-MM-DD). Mặc định: tự detect MAX(date)+1 per stock.',
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
        ticker = options['ticker']
        stock_type = options['stock_type']
        dry_run = options['dry_run']
        include_today = options['include_today']

        today = timezone.now().date()
        # Mặc định sync đến hôm nay (SSI thường có data EOD sau ~16:30)
        end_date = today
        # Parse --from-date nếu có
        forced_from_date = None
        if from_date_str:
            forced_from_date = date_type.fromisoformat(from_date_str)

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

        # 4. Sync cho từng stock
        total_created = 0
        total_skipped = 0
        errors = []

        for i, stk_ticker in enumerate(stock_tickers):
            if (i + 1) % 100 == 0 or i == 0:
                self.stdout.write(f"\n--- [{i+1}/{len(stock_tickers)}] ---")

            # Xác định from_date cho stock này
            if forced_from_date:
                stk_from = forced_from_date
            else:
                stk_last = last_dates.get(stk_ticker)
                if stk_last is None:
                    # Stock chưa có data trong MLStockData → skip (cần populate trước)
                    total_skipped += 1
                    continue
                stk_from = stk_last + timedelta(days=1)

            if stk_from > end_date:
                total_skipped += 1
                continue

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

    def _sync_stock(self, client, config, ticker, from_date, to_date, dry_run):
        """
        Lấy OHLCV + adj_close từ daily_stock_price API cho 1 mã,
        ghi vào MLStockData per chunk để theo dõi tiến độ.
        SSI API giới hạn ~30 ngày/request → chia thành chunks.
        Return: created_count
        """
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

            self.stdout.write(f"  {ticker}: chunk {chunk_num} ({chunk_start} → {chunk_end})...", ending="")
            self.stdout.flush()

            chunk_data = []
            page_index = 1
            page_size = 1000  # Lớn để giảm số API calls (SSI trả ALL stocks)
            consecutive_empty = 0  # Track pages không có data cho ticker

            while True:
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

                if not (_response_ok(response) and response.get('data')):
                    break

                page_data = response['data']
                found_in_page = 0
                for item in page_data:
                    parsed = _parse_stock_price_item(item, ticker)
                    if parsed is not None:
                        chunk_data.append(parsed)
                        found_in_page += 1

                if len(page_data) < page_size:
                    break  # Trang cuối cùng

                # SSI trả ALL stocks → nếu 2 trang liên tiếp không có
                # data cho ticker → đã quét đủ, stop
                if found_in_page == 0:
                    consecutive_empty += 1
                    if consecutive_empty >= 2:
                        break
                else:
                    consecutive_empty = 0

                # Đã tìm đủ data (28 ngày max ~22 ngày giao dịch)
                if len(chunk_data) >= 25:
                    break

                page_index += 1
                time.sleep(REQUEST_INTERVAL)

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
