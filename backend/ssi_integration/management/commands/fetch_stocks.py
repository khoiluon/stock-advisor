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

                req = securities(market=market, pageIndex=1, pageSize=1000)
                response = client.securities(config, req)

                response_status = response.get('status')
                if (response_status == 200 or str(response_status).lower() == 'success') and response.get('data'):
                    stocks_to_process = response['data']
                    self.stdout.write(f"Tìm thấy {len(stocks_to_process)} mã trên sàn {market}.")

                    for item in stocks_to_process:
                        ticker = item.get('Symbol')
                        if not ticker:
                            continue

                        # **LOGIC XỬ LÝ AN TOÀN HƠN**
                        # Lấy tên công ty, nếu là None thì chuyển thành chuỗi rỗng
                        company_name = item.get('StockName') or ''

                        stock_obj, created = Stock.objects.update_or_create(
                            ticker=ticker,
                            defaults={
                                'company_name': company_name,
                                'exchange': item.get('Market', 'OTHER'),
                            }
                        )

                        if created:
                            created_count += 1
                        else:
                            updated_count += 1
                else:
                    self.stderr.write(self.style.WARNING(
                        f"Không nhận được dữ liệu hoặc có lỗi cho sàn {market}. Response: {response}"))

            self.stdout.write(self.style.SUCCESS("Hoàn thành!"))
            self.stdout.write(f"- Đã tạo mới: {created_count} mã cổ phiếu.")
            self.stdout.write(f"- Đã cập nhật: {updated_count} mã cổ phiếu.")

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.stderr.write(self.style.ERROR(f"Đã xảy ra lỗi nghiêm trọng: {e}"))