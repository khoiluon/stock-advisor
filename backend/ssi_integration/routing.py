# ssi_integration/routing.py

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/stock/(?P<ticker>\w+)/$', consumers.StockDataConsumer.as_asgi()),
]