# backend/api/management/commands/ssi_listener.py

import os
import asyncio
import websockets
import json
import requests
from dotenv import load_dotenv
from django.core.management.base import BaseCommand
from channels.layers import get_channel_layer
from django.conf import settings

# Tải biến môi trường
dotenv_path = os.path.join(settings.BASE_DIR, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# --- CẤU HÌNH TẬP TRUNG ---
SSI_API_BASE_URL = "https://fc-data.ssi.com.vn/api/v2/"
# SỬA LỖI: URL WebSocket chuẩn thường không có tail path '/realtime' khi dùng raw socket
SSI_WSS_URL = "wss://fc-data.ssi.com.vn/"
CONSUMER_ID = os.getenv('SSI_FCDATA_CONSUMER_ID')
CONSUMER_SECRET = os.getenv('SSI_FCDATA_CONSUMER_SECRET')


class SSIApiClient:
    """Lớp quản lý việc tương tác với SSI REST API."""

    def __init__(self, base_url, consumer_id, consumer_secret):
        self.base_url = base_url
        self.consumer_id = consumer_id
        self.consumer_secret = consumer_secret

    def get_access_token(self):
        """Lấy Access Token mới."""
        token_url = f"{self.base_url}Market/AccessToken"
        payload = {"consumerID": self.consumer_id, "consumerSecret": self.consumer_secret}
        headers = {"Content-Type": "application/json"}
        self.log(f"--- Đang yêu cầu Access Token mới từ SSI... ---")
        try:
            response = requests.post(token_url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == 200 and data.get("data"):
                access_token = data["data"].get("accessToken")
                if access_token:
                    self.log("✅ Lấy Access Token thành công!")
                    return access_token
            self.log(f"❌ Lỗi logic từ API SSI khi lấy token: {data}")
            return None
        except requests.exceptions.RequestException as e:
            error_content = e.response.text if e.response else "No response"
            self.log(f"❌ Lỗi nghiêm trọng khi lấy Access Token: {e}. Response: {error_content}")
            return None

    def log(self, message):
        print(message)


class Command(BaseCommand):
    help = 'Connects to SSI WebSocket for real-time market data.'

    async def handle_async(self, *args, **options):
        channel_layer = get_channel_layer()
        ssi_client = SSIApiClient(SSI_API_BASE_URL, CONSUMER_ID, CONSUMER_SECRET)

        while True:
            # Lưu ý: requests là đồng bộ, nên chạy trong executor để tránh block event loop nếu cần thiết
            # Ở đây giữ nguyên cho đơn giản vì logic retry chịu lỗi được.
            access_token = ssi_client.get_access_token()

            if not access_token:
                self.stdout.write(self.style.ERROR("Không lấy được Access Token. Thử lại sau 30s..."))
                await asyncio.sleep(30)
                continue

            try:
                self.stdout.write(f"Đang kết nối tới: {SSI_WSS_URL}")
                # === KẾT NỐI WEBSOCKET ===
                async with websockets.connect(
                        SSI_WSS_URL,
                        extra_headers={'Authorization': f'Bearer {access_token}'},
                        ping_interval=None  # SSI đôi khi tự quản lý ping/pong, tắt ping client để tránh time out sai
                ) as websocket:
                    self.stdout.write(self.style.SUCCESS("✅ Đã kết nối tới SSI WebSocket!"))

                    await self.subscribe_to_channels(websocket)

                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            # SSI thường gửi heartbeat hoặc response connect data đầu tiên
                            if data.get('type') == 'error':
                                self.stdout.write(self.style.ERROR(f"Lỗi từ SSI: {data}"))
                                continue

                            if data.get('topic') or data.get('data'):
                                # Log gọn hơn để đỡ spam console
                                content = data.get('data')
                                self.stdout.write(f"Nhận data topic {data.get('topic')}")
                                await channel_layer.group_send(
                                    'market_data_group',
                                    {'type': 'send_market_data', 'data': data}
                                )
                        except json.JSONDecodeError:
                            self.stdout.write(self.style.WARNING(f"Nhận được tin nhắn không phải JSON: {message}"))

            except websockets.exceptions.InvalidStatusCode as e:
                self.stdout.write(
                    self.style.ERROR(f"Server từ chối kết nối (Mã lỗi {e.status_code}). Kiểm tra lại URL hoặc Token."))
                if e.status_code == 401:
                    self.stdout.write(self.style.WARNING("Token hết hạn hoặc không hợp lệ."))
            except websockets.exceptions.ConnectionClosed as e:
                self.stdout.write(self.style.WARNING(f"Mất kết nối WebSocket (Code: {e.code}). Đang kết nối lại..."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Lỗi không xác định: {e}. Đang kết nối lại sau 10s..."))

            await asyncio.sleep(10)

    async def subscribe_to_channels(self, websocket):
        subscribe_message = {
            "type": "sub",
            "data": {
                "channel": "market-data.match:symbol=FPT,VCB,HPG,MWG"
                # CÚ PHÁP: Lưu ý dấu ':' thay vì ';' tùy phiên bản API, nếu ';' không chạy hãy thử ':'
                # Thường SSI dùng 'market-data.match:symbol=...' hoặc format json khác.
                # Giữ nguyên code cũ nếu bạn chắc chắn đúng, ở đây chỉnh lại dấu hai chấm thường gặp hơn.
            }
        }
        # Thử fallback về format cũ nếu format trên không chạy
        # "channel": "market-data.match;symbol=..."

        await websocket.send(json.dumps(subscribe_message))
        self.stdout.write(self.style.NOTICE(f"-> Đã gửi yêu cầu sub: {subscribe_message['data']['channel']}"))

    def handle(self, *args, **options):
        asyncio.run(self.handle_async(*args, **options))
