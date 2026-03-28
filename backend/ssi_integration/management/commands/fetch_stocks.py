# ssi_integration/management/commands/fetch_stocks.py

from django.core.management.base import BaseCommand
from ssi_fc_data.fc_md_client import MarketDataClient
from ssi_fc_data.model.model import securities
from ssi_integration.ssi_config import get_ssi_config
from api.models import Stock


class Command(BaseCommand):
    help = 'Lấy và cập nhật danh sách tất cả các mã cổ phiếu từ SSI vào database'

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
                    req = securities(market=market, pageIndex=page_index, pageSize=page_size)
                    response = client.securities(config, req)

                    response_status = response.get('status')
                    if (response_status == 200 or str(response_status).lower() == 'success') and response.get('data'):
                        page_data = response['data']
                        all_stocks.extend(page_data)
                        self.stdout.write(f"  Trang {page_index}: {len(page_data)} mã")

                        # Nếu trả về ít hơn pageSize → đã hết data
                        if len(page_data) < page_size:
                            break
                        page_index += 1
                    else:
                        if page_index == 1:
                            self.stderr.write(self.style.WARNING(
                                f"Không nhận được dữ liệu cho sàn {market}. Response: {response}"))
                        break

                self.stdout.write(f"Tìm thấy tổng {len(all_stocks)} mã trên sàn {market}.")

                for item in all_stocks:
                    ticker = item.get('Symbol')
                    if not ticker:
                        continue

                    company_name = item.get('StockName') or ''
                    stock_type = item.get('StockType') or ''

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