"""
sync_stocks — Gộp fetch_stocks + fetch_stocks_full + prepare_ml_data thành 1 command duy nhất.

Quy trình:
1. Gọi SSI SecuritiesDetails API (có stock_type, pagination)
2. Lưu TẤT CẢ mã vào bảng Stock (3,489 mã: S, ETF, CW, bond...)
3. Đánh dấu stock_type để phân biệt ML-eligible (type='S') vs display-only

Usage:
    python manage.py sync_stocks
    python manage.py sync_stocks --market HOSE
    python manage.py sync_stocks --only-type S      # chỉ lưu cổ phiếu thường
"""
import time
from django.core.management.base import BaseCommand
from ssi_fc_data.fc_md_client import MarketDataClient
from ssi_fc_data.model.model import securities_details
from ssi_integration.ssi_config import get_ssi_config
from api.models import Stock

REQUEST_INTERVAL = 1.2
MAX_RETRIES_429 = 5
RETRY_BACKOFF_BASE = 1.5


class Command(BaseCommand):
    help = 'Đồng bộ danh sách cổ phiếu từ SSI (securities_details) vào bảng Stock'

    def add_arguments(self, parser):
        parser.add_argument(
            '--market', type=str, default=None,
            help='Chỉ đồng bộ 1 sàn (HOSE, HNX, UPCOM). Mặc định: tất cả.',
        )
        parser.add_argument(
            '--only-type', type=str, default=None,
            help='Chỉ lưu mã có SecType này (VD: S). Mặc định: lưu tất cả.',
        )

    @staticmethod
    def _extract_records(response_data):
        """Chuẩn hóa response từ SecuritiesDetails về list bản ghi."""
        if not response_data:
            return []
        if isinstance(response_data, list) and response_data and isinstance(response_data[0], dict):
            first = response_data[0]
            if 'RepeatedInfo' in first and isinstance(first.get('RepeatedInfo'), list):
                return first.get('RepeatedInfo') or []
            return response_data
        if isinstance(response_data, dict):
            repeated = response_data.get('RepeatedInfo')
            if isinstance(repeated, list):
                return repeated
        return []

    def _api_call_with_retry(self, client, config, req, context=""):
        """Gọi API với retry khi 429."""
        for attempt in range(MAX_RETRIES_429 + 1):
            response = client.securities_details(config, req)
            status = response.get('status')
            if status != 429:
                return response
            if attempt >= MAX_RETRIES_429:
                self.stderr.write(f"[WARN] {context}: Rate limit vượt {MAX_RETRIES_429} retry.")
                return response
            wait = RETRY_BACKOFF_BASE * (attempt + 1)
            self.stdout.write(f"  429 Rate limit {context}, retry {attempt+1}/{MAX_RETRIES_429} sau {wait:.1f}s...")
            time.sleep(wait)
        return {}

    def _fetch_market(self, client, config, market):
        """Lấy toàn bộ mã từ 1 sàn (có pagination)."""
        all_stocks = []
        page_index = 1
        page_size = 1000

        while True:
            req = securities_details(market=market, pageIndex=page_index, pageSize=page_size)
            response = self._api_call_with_retry(client, config, req, context=f"{market} p{page_index}")

            status = response.get('status')
            ok = status == 200 or str(status).lower() == 'success'
            if not (ok and response.get('data')):
                if page_index == 1:
                    self.stderr.write(self.style.WARNING(f"Không có data cho sàn {market}. Response: {response}"))
                break

            page_data = self._extract_records(response['data'])
            all_stocks.extend(page_data)
            self.stdout.write(f"  {market} trang {page_index}: {len(page_data)} mã")

            if len(page_data) < page_size:
                break
            page_index += 1
            time.sleep(REQUEST_INTERVAL)

        return all_stocks

    def handle(self, *args, **options):
        target_market = options.get('market')
        only_type = options.get('only_type')

        markets = [target_market] if target_market else ['HOSE', 'HNX', 'UPCOM']

        self.stdout.write("Đang khởi tạo SSI Client...")
        try:
            config = get_ssi_config()
            client = MarketDataClient(config)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Không thể khởi tạo SSI Client: {e}"))
            return

        # 1. Fetch all
        all_raw = []
        for market in markets:
            self.stdout.write(f"\nĐang tải sàn {market}...")
            records = self._fetch_market(client, config, market)
            all_raw.extend(records)
            time.sleep(REQUEST_INTERVAL)

        self.stdout.write(f"\nTổng tải về: {len(all_raw)} mã từ {len(markets)} sàn")

        # 2. Filter by type (optional)
        if only_type:
            only_type_upper = only_type.strip().upper()
            filtered = [s for s in all_raw if (s.get('SecType') or '').strip().upper() == only_type_upper]
            self.stdout.write(f"Lọc SecType='{only_type_upper}': {len(filtered)}/{len(all_raw)}")
            all_raw = filtered

        # 3. Save to Stock table
        created_count = 0
        updated_count = 0
        type_stats = {}

        for item in all_raw:
            ticker = item.get('Symbol')
            if not ticker:
                continue

            company_name = item.get('StockName') or item.get('SymbolName') or ''
            stock_type = (item.get('SecType') or '').strip().upper()
            exchange = item.get('Market') or item.get('Exchange') or 'OTHER'

            _, created = Stock.objects.update_or_create(
                ticker=ticker,
                defaults={
                    'company_name': company_name,
                    'exchange': exchange,
                    'stock_type': stock_type,
                    'is_active': True,
                }
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

            type_stats[stock_type] = type_stats.get(stock_type, 0) + 1

        # 4. Report
        self.stdout.write(self.style.SUCCESS(f"\nHoàn thành sync_stocks!"))
        self.stdout.write(f"  Tạo mới: {created_count}")
        self.stdout.write(f"  Cập nhật: {updated_count}")
        self.stdout.write(f"  Phân loại:")
        for stype, count in sorted(type_stats.items(), key=lambda x: -x[1]):
            label = "← ML eligible" if stype == 'S' else ""
            self.stdout.write(f"    {stype or '(empty)'}: {count} {label}")

        total_s = Stock.objects.filter(stock_type='S', is_active=True).count()
        total_all = Stock.objects.filter(is_active=True).count()
        self.stdout.write(f"\n  DB tổng active: {total_all} | stock_type='S': {total_s}")
