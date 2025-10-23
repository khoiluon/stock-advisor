# backend/test_ssi_connection.py

import os
import json
from dotenv import load_dotenv
# --- 1. IMPORT CLIENT CHÍNH THỨC ---
from ssi_fc_data.fc_md_stream import MarketDataStream
from ssi_fc_data.fc_md_client import MarketDataClient
from types import SimpleNamespace

# Tải biến môi trường
load_dotenv()
CONSUMER_ID = os.getenv('SSI_FCDATA_CONSUMER_ID')
CONSUMER_SECRET = os.getenv('SSI_FCDATA_CONSUMER_SECRET')


# --- HÀM CALLBACK ĐỂ XỬ LÝ TIN NHẮN REAL-TIME ---
def on_message(message):
    """
    Hàm này sẽ được tự động gọi mỗi khi có tin nhắn mới từ server.
    """
    print("\n--- Nhận được tin nhắn! ---")
    try:
        # Dữ liệu trả về có dạng {"DataType": "X", "Content": "{...}"}
        data = json.loads(message)
        data_type = data.get('DataType')
        content_str = data.get('Content')

        if content_str:
            # Parse chuỗi JSON bên trong Content
            content_data = json.loads(content_str)
            print(f"Loại dữ liệu: {data_type}")
            print("Nội dung:")
            # In ra cho đẹp
            print(json.dumps(content_data, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"Lỗi khi xử lý tin nhắn: {e}")
        print(f"Tin nhắn gốc: {message}")


def on_error(error):
    """Hàm callback để xử lý lỗi."""
    print(f"--- Gặp lỗi: {error} ---")


# --- HÀM CHÍNH ĐỂ CHẠY TEST ---
if __name__ == "__main__":
    if not all([CONSUMER_ID, CONSUMER_SECRET]):
        print("Lỗi: Không tìm thấy Consumer ID hoặc Secret trong file .env")
    else:
        # 2. TẠO ĐỐI TƯỢNG CONFIG "GIẢ LẬP"
        # Thư viện này đọc config từ một module, ta dùng SimpleNamespace để giả lập nó
        config = SimpleNamespace(
            consumerID=CONSUMER_ID,
            consumerSecret=CONSUMER_SECRET,
            # URL cho REST API
            url='https://fc-data.ssi.com.vn/api/',
            # URL cho Streaming
            stream_url='https://fc-datahub.ssi.com.vn/'
        )

        # 3. KHỞI TẠO CÁC CLIENT THEO ĐÚNG MẪU
        # MarketDataStream cần một MarketDataClient để tự lấy token
        rest_client = MarketDataClient(config)
        stream_client = MarketDataStream(config, rest_client)

        # 4. BẮT ĐẦU LẮNG NGHE DỮ LIỆU STREAMING
        print("\n--- Đang bắt đầu lắng nghe dữ liệu streaming... ---")
        print("Đăng ký kênh khớp lệnh (X) cho FPT và HPG.")
        print("Nhấn Ctrl+C để dừng.")

        # Kênh đăng ký: "DataType:Symbol1-Symbol2-..."
        channel = "X:FPT-HPG"

        # Bắt đầu streaming. Hàm này sẽ chạy vô tận.
        # Nó nhận 3 tham số: hàm xử lý message, hàm xử lý lỗi, và kênh đăng ký
        stream_client.start(on_message, on_error, channel)