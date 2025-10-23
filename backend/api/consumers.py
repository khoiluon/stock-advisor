# backend/api/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class MarketDataConsumer(AsyncWebsocketConsumer):
    # Được gọi khi trình duyệt kết nối tới
    async def connect(self):
        # Thêm kết nối này vào một "phòng chat" chung
        await self.channel_layer.group_add('market_data_group', self.channel_name)
        await self.accept()
        print(f"Client {self.channel_name} đã kết nối.")

    # Được gọi khi trình duyệt ngắt kết nối
    async def disconnect(self, close_code):
        # Rời khỏi "phòng chat"
        await self.channel_layer.group_discard('market_data_group', self.channel_name)
        print(f"Client {self.channel_name} đã ngắt kết nối.")

    # Hàm này được gọi bởi "Người Lắng nghe" (ssi_listener)
    # Tên hàm phải khớp với 'type' trong group_send
    async def send_market_data(self, event):
        data = event['data']
        # Gửi dữ liệu nhận được xuống cho trình duyệt
        await self.send(text_data=json.dumps(data))