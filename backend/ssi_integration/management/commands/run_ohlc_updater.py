# ssi_integration/management/commands/run_ohlc_updater.py

import json
import time
from datetime import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from ssi_fc_data.fc_md_stream import MarketDataStream
from ssi_fc_data.fc_md_client import MarketDataClient
from ssi_integration.ssi_config import get_ssi_config
from api.models import Stock, StockData

# --- State trong bộ nhớ để tổng hợp dữ liệu OHLC ---
# Cấu trúc: {'FPT': {'open': 100, 'high': 102, 'low': 99, 'close': 101, 'volume': 15000}, ...}
DAILY_OHLC_CACHE = {}
LAST_DB_UPDATE = time.time()
UPDATE_INTERVAL = 60  # Cập nhật vào DB mỗi 60 giây


def ssi_message_handler(message):
    """
    Hàm callback được gọi mỗi khi có tin nhắn từ SSI.
    Nó sẽ cập nhật dữ liệu OHLC trong cache.
    """
    global DAILY_OHLC_CACHE

    try:
        data_type = message.get('DataType')

        if data_type == 'X-TRADE' and message.get('Content'):
            content = json.loads(message['Content'])

            ticker = content.get('Symbol')
            price = Decimal(str(content.get('LastPrice', 0)))
            volume = int(content.get('LastVol', 0))

            if not ticker or price == 0 or volume == 0:
                return

            # Lấy hoặc tạo mới entry trong cache
            stock_cache = DAILY_OHLC_CACHE.get(ticker)

            if stock_cache is None:
                # Lần giao dịch đầu tiên trong ngày của mã này
                DAILY_OHLC_CACHE[ticker] = {
                    'open': price,
                    'high': price,
                    'low': price,
                    'close': price,
                    'volume': volume,
                }
            else:
                # Cập nhật các giá trị
                stock_cache['high'] = max(stock_cache['high'], price)
                stock_cache['low'] = min(stock_cache['low'], price)
                stock_cache['close'] = price
                stock_cache['volume'] += volume

    except Exception as e:
        print(f"Lỗi xử lý tin nhắn: {e} - Message: {message}")


def update_database():
    """
    Lấy dữ liệu từ cache và cập nhật hàng loạt vào database.
    """
    global DAILY_OHLC_CACHE, LAST_DB_UPDATE

    if not DAILY_OHLC_CACHE:
        return

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Chuẩn bị cập nhật {len(DAILY_OHLC_CACHE)} mã vào database...")

    # Lấy danh sách các mã cổ phiếu có trong cache
    tickers_in_cache = list(DAILY_OHLC_CACHE.keys())
    stocks = Stock.objects.filter(ticker__in=tickers_in_cache)
    stock_map = {stock.ticker: stock for stock in stocks}

    today = timezone.now().date()

    for ticker, ohlc_data in DAILY_OHLC_CACHE.items():
        stock_instance = stock_map.get(ticker)
        if not stock_instance:
            continue  # Bỏ qua nếu mã không có trong bảng Stock

        try:
            # Dùng update_or_create để tạo mới hoặc cập nhật bản ghi của ngày hôm nay
            StockData.objects.update_or_create(
                stock=stock_instance,
                date=today,
                defaults={
                    'open': ohlc_data['open'],
                    'high': ohlc_data['high'],
                    'low': ohlc_data['low'],
                    'close': ohlc_data['close'],
                    'volume': ohlc_data['volume'],
                }
            )
        except Exception as e:
            print(f"Lỗi khi cập nhật mã {ticker}: {e}")

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Đã cập nhật xong.")
    LAST_DB_UPDATE = time.time()


class Command(BaseCommand):
    help = 'Chạy worker để tổng hợp và cập nhật dữ liệu OHLC hàng ngày từ SSI'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Đang khởi động OHLC Updater Worker..."))

        try:
            config = get_ssi_config()
            client = MarketDataClient(config)
            stream = MarketDataStream(config, client)

            channel = 'X:ALL'
            self.stdout.write(f"Đang đăng ký kênh: {channel}")

            stream.start(ssi_message_handler, lambda err: print(f"Lỗi kết nối: {err}"), channel)

            self.stdout.write(self.style.SUCCESS("Worker đã kết nối. Đang tổng hợp dữ liệu... (Nhấn Ctrl+C để dừng)"))

            while True:
                time.sleep(1)
                # Định kỳ cập nhật vào database
                if (time.time() - LAST_DB_UPDATE) > UPDATE_INTERVAL:
                    update_database()

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\nĐang dừng worker và lưu dữ liệu cuối cùng..."))
            update_database()  # Cố gắng lưu nốt dữ liệu cuối cùng
            self.stdout.write(self.style.SUCCESS("Worker đã dừng."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Worker gặp lỗi nghiêm trọng: {e}"))