# ssi_integration/management/commands/fetch_stocks.py

from django.core.management.base import BaseCommand
import time
from ssi_fc_data.fc_md_client import MarketDataClient
from ssi_fc_data.model.model import securities_details
from ssi_integration.ssi_config import get_ssi_config
from api.models import Stock


REQUEST_INTERVAL_SECONDS = 1.2
MAX_RETRIES_429 = 5
RETRY_BACKOFF_BASE_SECONDS = 1.5


class Command(BaseCommand):
    help = 'Lấy và cập nhật danh sách tất cả các mã cổ phiếu từ SSI vào database'

    @staticmethod
    def _extract_records(response_data):
        """Chuẩn hóa response từ SecuritiesDetails về list bản ghi symbol."""
        if not response_data:
            return []

        # Trường hợp API trả trực tiếp list[dict symbol]
        if isinstance(response_data, list) and response_data and isinstance(response_data[0], dict):
            first = response_data[0]
            # Trường hợp SecuritiesDetails trả wrapper: [{..., 'RepeatedInfo': [...]}]
            if 'RepeatedInfo' in first and isinstance(first.get('RepeatedInfo'), list):
                return first.get('RepeatedInfo') or []
            return response_data

        # Trường hợp API trả dict có RepeatedInfo
        if isinstance(response_data, dict):
            repeated = response_data.get('RepeatedInfo')
            if isinstance(repeated, list):
                return repeated

        return []

    def handle(self, *args, **options):
        self.stdout.write("Đang kết nối tới SSI để lấy danh sách cổ phiếu...")

        try:
            config = get_ssi_config()
            client = MarketDataClient(config)

            markets = ['HOSE', 'HNX', 'UPCOM']
            created_count = 0
            updated_count = 0

            for market in markets:
                self.stdout.write(f"Đang xử lý dữ liệu cho sàn {market}...")

                page_index = 1
                page_size = 1000
                all_stocks = []

                # Pagination loop — lấy hết tất cả các trang
                while True:
                    req = securities_details(market=market, pageIndex=page_index, pageSize=page_size)
                    response = None

                    for retry_idx in range(MAX_RETRIES_429 + 1):
                        response = client.securities_details(config, req)
                        response_status = response.get('status')

                        if response_status != 429:
                            break

                        if retry_idx >= MAX_RETRIES_429:
                            self.stderr.write(self.style.ERROR(
                                f"Rate limit vượt quá số lần retry ở sàn {market}, trang {page_index}."
                            ))
                            break

                        wait_seconds = RETRY_BACKOFF_BASE_SECONDS * (retry_idx + 1)
                        self.stdout.write(
                            f"  Rate limit 429 tại {market} trang {page_index}. "
                            f"Retry {retry_idx + 1}/{MAX_RETRIES_429} sau {wait_seconds:.1f}s..."
                        )
                        time.sleep(wait_seconds)

                    if response is None:
                        break

                    response_status = response.get('status')
                    if (response_status == 200 or str(response_status).lower() == 'success') and response.get('data'):
                        page_data = self._extract_records(response['data'])
                        all_stocks.extend(page_data)
                        self.stdout.write(f"  Trang {page_index}: {len(page_data)} mã")
                        time.sleep(REQUEST_INTERVAL_SECONDS)

                        # Nếu trả về ít hơn pageSize → đã hết data
                        if len(page_data) < page_size:
                            break
                        page_index += 1
                    else:
                        if page_index == 1:
                            self.stderr.write(self.style.WARNING(
                                f"Không nhận được dữ liệu cho sàn {market}. Response: {response}"))
                        break

                time.sleep(REQUEST_INTERVAL_SECONDS)

                self.stdout.write(f"Tìm thấy tổng {len(all_stocks)} mã trên sàn {market}.")

                for item in all_stocks:
                    ticker = item.get('Symbol')
                    if not ticker:
                        continue

                    company_name = item.get('StockName') or item.get('SymbolName') or ''
                    stock_type = (item.get('SecType') or '').strip().upper()

                    stock_obj, created = Stock.objects.update_or_create(
                        ticker=ticker,
                        defaults={
                            'company_name': company_name,
                            'exchange': item.get('Market', 'OTHER'),
                            'stock_type': stock_type,
                        }
                    )

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

            self.stdout.write(self.style.SUCCESS("Hoàn thành!"))
            self.stdout.write(f"- Đã tạo mới: {created_count} mã cổ phiếu.")
            self.stdout.write(f"- Đã cập nhật: {updated_count} mã cổ phiếu.")

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.stderr.write(self.style.ERROR(f"Đã xảy ra lỗi nghiêm trọng: {e}"))