# ssi_integration/management/commands/backfill_ohlc.py

import time
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.db.models import Avg, Count
from api.models import Stock, StockData
from ssi_integration.services import update_historical_data_with_client
from ssi_fc_data.fc_md_client import MarketDataClient
from ssi_integration.ssi_config import get_ssi_config

# --- CÁC HẰNG SỐ CHO BỘ LỌC ---
MIN_AVG_VOLUME = 50000
MIN_TRADING_DAYS_YEAR = 250

class Command(BaseCommand):
    help = 'Tải dữ liệu lịch sử và lọc các mã đạt chuẩn cho ML.'

    def add_arguments(self, parser):
        parser.add_argument("--ticker", help="Chỉ chạy cho 1 mã cụ thể, ví dụ: FPT")

    def handle(self, *args, **options):
        # Bắt đầu với tất cả các mã được cho là active
        queryset = Stock.objects.filter(is_active=True).order_by("ticker")

        ticker_option = options.get("ticker")
        if ticker_option:
            queryset = queryset.filter(ticker=ticker_option.upper())

        all_tickers = list(queryset.values_list('ticker', flat=True))
        total_stocks = len(all_tickers)

        if total_stocks == 0:
            self.stdout.write(self.style.WARNING("Không có mã nào (is_active=True) để xử lý."))
            return
        
        self.stdout.write(f"Bắt đầu quá trình tải và lọc cho {total_stocks} mã ứng viên...")
        start_time = time.time()
        
        try:
            self.stdout.write("Đang khởi tạo SSI Client...")
            config = get_ssi_config()
            client = MarketDataClient(config)
            self.stdout.write(self.style.SUCCESS("Khởi tạo Client thành công."))

            qualified_count = 0
            disqualified_count = 0

            for i, ticker in enumerate(all_tickers):
                self.stdout.write(f"\n--- Xử lý mã {i+1}/{total_stocks}: {ticker} ---")
                
                # 1. Tải dữ liệu lịch sử
                try:
                    update_historical_data_with_client(client, config, ticker)
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Gặp lỗi khi tải dữ liệu cho {ticker}: {e}"))
                    continue # Bỏ qua mã này

                # 2. Thực hiện kiểm tra sau khi tải
                is_qualified, reason = self.validate_stock_data(ticker)

                # 3. Cập nhật trạng thái
                if is_qualified:
                    self.stdout.write(self.style.SUCCESS(f"-> ĐẠT CHUẨN. {reason}"))
                    qualified_count += 1
                else:
                    self.stdout.write(self.style.WARNING(f"-> LOẠI. Lý do: {reason}"))
                    # Đánh dấu là inactive và có thể xóa dữ liệu để tiết kiệm dung lượng
                    Stock.objects.filter(ticker=ticker).update(is_active=False)
                    # StockData.objects.filter(stock__ticker=ticker).delete() # Bỏ comment dòng này nếu muốn xóa data
                    disqualified_count += 1

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Lỗi nghiêm trọng khi khởi tạo SSI Client: {e}"))
            return

        total_time = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(f"\n--- HOÀN THÀNH ---"))
        self.stdout.write(f"Tổng thời gian: {total_time:.2f} giây.")
        self.stdout.write(f"Số mã đạt chuẩn: {qualified_count}")
        self.stdout.write(f"Số mã bị loại: {disqualified_count}")

    def validate_stock_data(self, ticker):
        """Kiểm tra dữ liệu đã tải của một mã có đạt chuẩn không."""
        
        # Kiểm tra tuổi đời
        trading_days_count = StockData.objects.filter(stock__ticker=ticker).count()
        if trading_days_count < MIN_TRADING_DAYS_YEAR:
            return False, f"Tuổi đời quá ngắn ({trading_days_count} < {MIN_TRADING_DAYS_YEAR} ngày)"

        # Kiểm tra thanh khoản 30 ngày gần nhất
        thirty_days_ago = date.today() - timedelta(days=45) # Lấy 45 ngày để đảm bảo có 30 phiên
        recent_data = StockData.objects.filter(
            stock__ticker=ticker,
            date__gte=thirty_days_ago
        ).aggregate(
            avg_volume=Avg('volume'),
            count=Count('id')
        )
        
        avg_volume = recent_data.get('avg_volume') or 0
        
        if avg_volume < MIN_AVG_VOLUME:
            return False, f"Thanh khoản thấp (Volume TB {avg_volume:,.0f} < {MIN_AVG_VOLUME:,})"
            
        return True, f"Tuổi đời: {trading_days_count} ngày, Volume TB: {avg_volume:,.0f}"