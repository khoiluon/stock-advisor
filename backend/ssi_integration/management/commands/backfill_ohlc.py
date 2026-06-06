# ssi_integration/management/commands/backfill_ohlc.py

import time
from django.core.management.base import BaseCommand
from api.models import Stock
from ssi_integration.services import update_historical_data


class Command(BaseCommand):
    help = 'Tải toàn bộ dữ liệu lịch sử OHLC cho tất cả các mã cổ phiếu trong bảng Stock.'

    def handle(self, *args, **options):
        # Lấy danh sách tất cả các ticker từ bảng Stock
        all_tickers = list(Stock.objects.values_list('ticker', flat=True))
        total_stocks = len(all_tickers)

        self.stdout.write(f"Tìm thấy {total_stocks} mã cổ phiếu trong database.")
        self.stdout.write("Bắt đầu quá trình tải dữ liệu lịch sử. Quá trình này có thể mất rất nhiều thời gian...")

        for i, ticker in enumerate(all_tickers):
            self.stdout.write(f"\n--- Đang xử lý mã {i + 1}/{total_stocks}: {ticker} ---")

            try:
                # Gọi hàm service mà chúng ta đã viết trước đó
                update_historical_data(ticker)

                # Tạm dừng 1 giây để tránh bị rate limit bởi server SSI
                self.stdout.write("Tạm dừng 1 giây...")
                time.sleep(1)

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Gặp lỗi khi xử lý mã {ticker}: {e}"))
                self.stdout.write("Tiếp tục với mã tiếp theo sau 5 giây...")
                time.sleep(5)

        self.stdout.write(self.style.SUCCESS("\nHoàn thành quá trình tải dữ liệu lịch sử cho tất cả các mã!"))