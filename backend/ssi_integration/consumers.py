# ssi_integration/consumers.py

import json
import threading
import time  # Thêm import time
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from ssi_fc_data.fc_md_stream import MarketDataStream
from ssi_fc_data.fc_md_client import MarketDataClient
from .ssi_config import get_ssi_config


class StockDataConsumer(WebsocketConsumer):
    def connect(self):
        self.ticker = self.scope['url_route']['kwargs']['ticker']
        self.room_group_name = f'stock_{self.ticker}'
        self.is_running = True  # Cờ để điều khiển thread

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

        self.ssi_stream_thread = threading.Thread(target=self.start_ssi_stream)
        self.ssi_stream_thread.daemon = True
        self.ssi_stream_thread.start()

    def disconnect(self, close_code):
        self.is_running = False  # Dừng thread
        # Cần có cơ chế để dừng hẳn đối tượng stream, nhưng tạm thời cờ này sẽ ngăn gửi message
        print(f"WebSocket disconnected for {self.ticker}")
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    def _ssi_message_handler(self, message):
        if self.is_running:  # Chỉ gửi nếu client vẫn đang kết nối
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'stock_update',
                    'message': message
                }
            )

    def _ssi_error_handler(self, error):
        print(f"SSI Stream Error for {self.ticker}: {error}")

    def start_ssi_stream(self):
        try:
            config = get_ssi_config()
            client = MarketDataClient(config)
            self.stream = MarketDataStream(config, client)  # Lưu stream vào self

            channel = f"B:{self.ticker.upper()}"
            print(f"Starting SSI stream for channel: {channel}")

            self.stream.start(self._ssi_message_handler, self._ssi_error_handler, channel)

            # Vòng lặp giữ thread sống và kiểm tra cờ is_running
            while self.is_running:
                time.sleep(1)

            print(f"Stopping SSI stream for {self.ticker}")
            # Thư viện ssi-fc-data không có hàm stop() rõ ràng,
            # việc thread kết thúc sẽ giúp giải phóng tài nguyên.

        except Exception as e:
            print(f"Failed to start SSI stream for {self.ticker}: {e}")

    def stock_update(self, event):
        message = event['message']
        self.send(text_data=json.dumps(message))