# ssi_integration/management/commands/prepare_ml_data.py

import time
from django.core.management.base import BaseCommand
from ssi_fc_data.fc_md_client import MarketDataClient
from ssi_fc_data.model.model import securities_details
from ssi_integration.ssi_config import get_ssi_config
from api.models import Stock
from ssi_integration.services import _throttled_request, _response_ok

class Command(BaseCommand):
    help = 'Tải danh sách các mã cổ phiếu thường (ứng viên) từ SSI.'

    def handle(self, *args, **options):
        self.stdout.write("Đang khởi tạo SSI Client...")
        try:
            config = get_ssi_config()
            client = MarketDataClient(config)
            self.stdout.write(self.style.SUCCESS("Khởi tạo Client thành công."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Không thể khởi tạo SSI Client: {e}"))
            return

        # GIAI ĐOẠN 1: TẢI DỮ LIỆU THÔ
        self.stdout.write("\n--- GIAI ĐOẠN 1: Tải danh sách mã thô từ SSI ---")
        raw_stocks = self.fetch_raw_stocks(client, config)
        self.stdout.write(f"Đã tải về thông tin của {len(raw_stocks)} mã chứng khoán.")

        # GIAI ĐOẠN 2: LỌC CƠ BẢN VÀ LƯU
        self.stdout.write("\n--- GIAI ĐOẠN 2: Lọc cổ phiếu thường và lưu vào DB ---")
        stock_candidates = [s for s in raw_stocks if (s.get('SecType') or '').strip().upper() == 'S']
        self.stdout.write(f"Tìm thấy {len(stock_candidates)} mã là cổ phiếu thường.")
        
        self.save_candidate_stocks(stock_candidates)
        self.stdout.write(self.style.SUCCESS("\nHoàn thành việc lưu danh sách ứng viên!"))

    def fetch_raw_stocks(self, client, config):
        all_stocks = []
        for market in ['HOSE', 'HNX', 'UPCOM']:
            self.stdout.write(f"  Đang tải dữ liệu sàn {market}...")
            req = securities_details(market=market, pageIndex=1, pageSize=1000)
            response = _throttled_request(client.securities_details, config, req, context=f"SecuritiesDetails {market}")
            if _response_ok(response) and response.get('data'):
                data_list = response['data']
                if data_list and 'RepeatedInfo' in data_list[0]:
                    all_stocks.extend(data_list[0]['RepeatedInfo'])
        return all_stocks

    def save_candidate_stocks(self, stocks):
        created_count, updated_count = 0, 0
        
        for item in stocks:
            ticker = item.get('Symbol')
            if not ticker: continue

            _, created = Stock.objects.update_or_create(
                ticker=ticker,
                defaults={
                    'company_name': item.get('SymbolName', ''),
                    'exchange': item.get('Exchange', 'OTHER'),
                    'stock_type': (item.get('SecType') or '').strip().upper(),
                    'is_active': True, # Mặc định coi tất cả là ứng viên tiềm năng
                }
            )
            if created: created_count += 1
            else: updated_count += 1
        
        self.stdout.write(f"Đã lưu vào DB. Tạo mới: {created_count}, Cập nhật: {updated_count}.")
        self.stdout.write(f"Tổng số mã ứng viên (is_active=True): {len(stocks)}.")