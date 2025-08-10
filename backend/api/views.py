from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.generics import RetrieveAPIView
from django.contrib.auth.models import User
from .serializers import RegisterSerializer, StockSerializer, WatchlistSerializer
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from vnstock import Vnstock
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta
import os
from django.conf import settings
from unidecode import unidecode
from .models import Stock, StockData, Watchlist, Alert, PotentialStock


# CreateAPIView cung cấp sẵn phương thức POST để tạo mới một đối tượng
class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class StockDataAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ticker_symbol = request.query_params.get('ticker', 'FPT').upper()

        try:
            # Bước 1: Truy vấn dữ liệu từ database, cực kỳ nhanh chóng
            queryset = StockData.objects.filter(stock__ticker=ticker_symbol).order_by('date')

            if not queryset.exists():
                return Response(
                    {"error": f"Không tìm thấy dữ liệu cho mã {ticker_symbol} trong database."},
                    status=status.HTTP_404_NOT_FOUND)

            # Bước 2: Chuyển queryset thành DataFrame của Pandas để tính toán
            df = pd.DataFrame(list(queryset.values('date', 'open', 'high', 'low', 'close', 'volume')))

            # Đổi tên cột để pandas_ta có thể nhận diện
            df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'},
                      inplace=True)

            # Bước 3: Tính toán các chỉ báo kỹ thuật
            df.ta.macd(close='Close', fast=12, slow=26, signal=9, append=True)
            df.ta.rsi(close='Close', length=14, append=True)
            df.ta.sma(close='Close', length=20, append=True)
            df.ta.sma(close='Close', length=50, append=True)

            # Bước 4: Hoàn thiện dữ liệu trước khi trả về
            df.dropna(inplace=True)  # Bỏ các dòng đầu tiên không đủ dữ liệu tính chỉ báo
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')  # Chuẩn hóa định dạng ngày

            data = df.to_dict(orient='records')
            return Response(data)

        except Exception as e:
            return Response({"error": f"Đã xảy ra lỗi không xác định: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StockListAPIView(generics.ListAPIView):
    """
    API cung cấp danh sách tất cả các mã cổ phiếu có trong hệ thống.
    Hữu ích cho việc tìm kiếm hoặc điền vào dropdown trên frontend.
    """
    queryset = Stock.objects.all().order_by('ticker')
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]

class StockDetailAPIView(RetrieveAPIView):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'ticker'

# API cho danh sách yêu thích (Watchlist)
class WatchlistListCreateView(generics.ListCreateAPIView):
    serializer_class = WatchlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Watchlist.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

from rest_framework import status
from rest_framework.views import APIView
class WatchlistDeleteView(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request, pk):
        try:
            watch = Watchlist.objects.get(pk=pk, user=request.user)
            watch.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Watchlist.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)