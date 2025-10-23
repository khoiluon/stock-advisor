# backend/api/management/commands/ssi_listener.py

import os
import asyncio
import websockets # <-- Sẽ dùng phiên bản 11.0.3
import json
import requests
from dotenv import load_dotenv
from django.core.management.base import BaseCommand
from channels.layers import get_channel_layer
from django.conf import settings

# Tải biến môi trường một cách bền vững
dotenv_path = os.path.join(settings.BASE_DIR, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# --- CẤU HÌNH TẬP TRUNG ---
SSI_API_BASE_URL = "https://fc-data.ssi.com.vn/api/v2/"
SSI_WSS_URL = "wss://fc-data.ssi.com.vn/realtime"
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
        print("--- Đang yêu cầu Access Token mới từ SSI... ---")
        try:
            response = requests.post(token_url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == 200 and data.get("data"):
                access_token = data["data"].get("accessToken")
                if access_token:
                    print("✅ Lấy Access Token thành công!")
                    return access_token
            print(f"❌ Lỗi logic từ API SSI khi lấy token: {data}")
            return None
        except requests.exceptions.RequestException as e:
            error_content = e.response.text if e.response else "No response"
            print(f"❌ Lỗi nghiêm trọng khi lấy Access Token: {e}. Response: {error_content}")
            return None

class Command(BaseCommand):
    help = 'Connects to SSI WebSocket for real-time market data.'

    async def handle_async(self, *args, **options):
        channel_layer = get_channel_layer()
        ssi_client = SSIApiClient(SSI_API_BASE_URL, CONSUMER_ID, CONSUMER_SECRET)

        while True:
            access_token = ssi_client.get_access_token()
            if not access_token:
                self.stdout.write(self.style.ERROR("Không lấy được Access Token. Thử lại sau 30s..."))
                await asyncio.sleep(30)
                continue

            try:
                # === CÚ PHÁP ĐÚNG CHO WEBSOCKETS v11.x ===
                # Tham số `extra_headers` là cách truyền header chính xác
                async with websockets.connect(SSI_WSS_URL, extra_headers={'Authorization': f'Bearer {access_token}'}) as websocket:
                # =========================================
                    self.stdout.write(self.style.SUCCESS("✅ Đã kết nối tới SSI WebSocket!"))
                    await self.subscribe_to_channels(websocket)

                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            if data.get('topic') or data.get('data'):
                                self.stdout.write(f"Nhận được data: {json.dumps(data)}")
                                await channel_layer.group_send(
                                    'market_data_group',
                                    {'type': 'send_market_data', 'data': data}
                                )
                        except json.JSONDecodeError:
                            self.stdout.write(self.style.WARNING(f"Nhận được tin nhắn không phải JSON: {message}"))

            # === SỬ DỤNG EXCEPTION ĐÚNG TỪ WEBSOCKETS v11.x ===
            except websockets.exceptions.ConnectionClosed as e:
            # =================================================
                if "401" in str(e):
                    self.stdout.write(self.style.WARNING("Token có thể đã hết hạn. Yêu cầu token mới..."))
                else:
                    self.stdout.write(self.style.WARNING(f"Mất kết nối WebSocket: {e}. Đang kết nối lại..."))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Lỗi không xác định: {e}. Đang kết nối lại sau 10s..."))

            await asyncio.sleep(5)

    async def subscribe_to_channels(self, websocket):
        subscribe_message = {
            "type": "sub",
            "data": {
                "channel": "market-data.match;symbol=FPT,VCB,HPG,MWG"
            }
        }
        await websocket.send(json.dumps(subscribe_message))
        self.stdout.write(self.style.NOTICE(f"-> Đã gửi yêu cầu theo dõi kênh: {subscribe_message['data']['channel']}"))

    def handle(self, *args, **options):
        asyncio.run(self.handle_async(*args, **options))