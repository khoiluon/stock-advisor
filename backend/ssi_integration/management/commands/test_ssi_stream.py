# ssi_integration/management/commands/test_ssi_stream.py

import time
import json
from django.core.management.base import BaseCommand
from ssi_fc_data.fc_md_stream import MarketDataStream
from ssi_fc_data.fc_md_client import MarketDataClient
from ssi_integration.ssi_config import get_ssi_config

# Hàm callback để xử lý message nhận được từ stream
def get_market_data(message):
    """
    Hàm này sẽ được gọi mỗi khi có dữ liệu mới từ SSI.
    'message' là một dict đã được parse từ JSON.
    """
    # In ra console dưới dạng JSON đẹp mắt
    print(json.dumps(message, indent=2, ensure_ascii=False))

# Hàm callback để xử lý lỗi
def get_error(error):
    """Hàm này sẽ được gọi khi có lỗi xảy ra."""
    print(f"LỖI STREAMING: {error}")

class Command(BaseCommand):
    help = 'Mở một kết nối streaming tới SSI FastConnect Data để test.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Đang chuẩn bị kết nối tới SSI..."))

        try:
            # 1. Lấy cấu hình từ settings.py
            ssi_config = get_ssi_config()

            # 2. Khởi tạo MarketDataClient để lấy access token
            self.stdout.write("Đang lấy access token...")
            md_client = MarketDataClient(ssi_config)
            self.stdout.write(self.style.SUCCESS("Lấy access token thành công!"))

            # 3. Khởi tạo MarketDataStream
            md_stream = MarketDataStream(ssi_config, md_client)

            # 4. Nhập kênh muốn theo dõi
            self.stdout.write("="*50)
            self.stdout.write("Nhập kênh bạn muốn theo dõi (ví dụ: 'X:ALL', 'MI:VN30', 'B:SSI')")
            selected_channel = input("Nhập kênh: ")

            # 5. Bắt đầu lắng nghe stream
            self.stdout.write(self.style.SUCCESS(f"Đang bắt đầu lắng nghe kênh '{selected_channel}'..."))
            md_stream.start(get_market_data, get_error, selected_channel)

            # 6. Giữ cho script chạy để nhận dữ liệu
            self.stdout.write(self.style.WARNING("Đã kết nối. Nhấn Ctrl+C để dừng lại."))
            while True:
                time.sleep(1)

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Đã xảy ra lỗi: {e}"))
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS("\nĐã dừng script."))