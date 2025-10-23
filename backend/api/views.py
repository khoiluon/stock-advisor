# api/views.py

from django.contrib.auth.models import User
from django.db.models import Q
from django.db.models.functions import Length
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
import pandas as pd
import pandas_ta as ta

from .models import Stock, StockData, Watchlist, PotentialStock, Article
from .pagination import StandardResultsSetPagination
from .serializers import (
    RegisterSerializer, StockSerializer, WatchlistSerializer,
    ArticleSerializer, PotentialStockSerializer, StockDataSerializer
)
# Import hàm lấp đầy khoảng trống
from ssi_integration.services import update_historical_data


# ==============================================================================
# VIEWS CHO USER VÀ CÁC TÍNH NĂNG KHÁC (Giữ nguyên)
# ==============================================================================

class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class StockListAPIView(generics.ListAPIView):
    queryset = Stock.objects.all().order_by('ticker')
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]


class StockDetailAPIView(generics.RetrieveAPIView):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'ticker'


class WatchlistListCreateView(generics.ListCreateAPIView):
    serializer_class = WatchlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Watchlist.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WatchlistDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            watch = Watchlist.objects.get(pk=pk, user=request.user)
            watch.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Watchlist.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)


class ArticleListAPIView(generics.ListAPIView):
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Article.objects.all()
        ticker = self.request.query_params.get('ticker', None)
        if ticker is not None:
            queryset = queryset.filter(related_stocks__ticker=ticker.upper())
        return queryset


class StockScreenerAPIView(generics.ListAPIView):
    serializer_class = PotentialStockSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        latest_date = PotentialStock.objects.order_by('-analysis_date').values_list('analysis_date', flat=True).first()
        if not latest_date:
            return PotentialStock.objects.none()
        queryset = PotentialStock.objects.filter(analysis_date=latest_date)
        timeframe = self.request.query_params.get('timeframe', None)
        if timeframe:
            queryset = queryset.filter(timeframe=timeframe)
        return queryset


class StockSearchAPIView(generics.ListAPIView):
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        query = self.request.query_params.get('q', '').upper()
        if not query:
            return Stock.objects.none()
        exact_match = Stock.objects.filter(ticker__exact=query)
        starts_with_matches = Stock.objects.filter(ticker__startswith=query).exclude(ticker__exact=query).order_by(
            Length('ticker'))
        company_name_matches = Stock.objects.filter(company_name__icontains=query).exclude(ticker__exact=query).exclude(
            ticker__startswith=query)

        seen_tickers = set()
        combined_results = []
        for stock in list(exact_match) + list(starts_with_matches) + list(company_name_matches):
            if stock.ticker not in seen_tickers:
                combined_results.append(stock)
                seen_tickers.add(stock.ticker)
        return combined_results[:10]


# ==============================================================================
# STOCK DATA VIEW (ĐÃ ĐƯỢC HỢP NHẤT VÀ TỐI ƯU)
# ==============================================================================

class StockDataAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ticker_symbol = request.query_params.get('ticker', 'FPT').upper()

        try:
            # BƯỚC 1: Lấp đầy khoảng trống dữ liệu bằng cách gọi API SSI
            update_historical_data(ticker_symbol)

            # BƯỚC 2: Truy vấn toàn bộ dữ liệu (cũ + mới) từ database
            queryset = StockData.objects.filter(stock__ticker=ticker_symbol).order_by('date')

            if not queryset.exists():
                return Response(
                    {"error": f"Không tìm thấy dữ liệu cho mã {ticker_symbol} trong database."},
                    status=status.HTTP_404_NOT_FOUND)

            # BƯỚC 3: Chuyển dữ liệu sang Pandas DataFrame để tính toán
            # Quan trọng: Dùng serializer để lấy đúng kiểu dữ liệu (Decimal -> float)
            serializer = StockDataSerializer(queryset, many=True)
            df = pd.DataFrame(serializer.data)

            # Đảm bảo các cột có đúng kiểu dữ liệu số
            ohlcv_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in ohlcv_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # BƯỚC 4: Tính toán các chỉ báo kỹ thuật bằng pandas_ta
            # Thư viện này tự động tìm các cột 'open', 'high', 'low', 'close', 'volume'
            df.ta.macd(fast=12, slow=26, signal=9, append=True)
            df.ta.rsi(length=14, append=True)
            df.ta.bbands(length=20, std=2, append=True)
            # Bạn có thể thêm các chỉ báo khác ở đây, ví dụ:
            # df.ta.sma(length=20, append=True)
            # df.ta.sma(length=50, append=True)

            # BƯỚC 5: Hoàn thiện dữ liệu trước khi trả về
            df.dropna(inplace=True)  # Bỏ các dòng đầu tiên không đủ dữ liệu tính chỉ báo

            # Chuyển DataFrame thành danh sách các dictionary để trả về JSON
            data = df.to_dict(orient='records')
            return Response(data)

        except Exception as e:
            # Ghi lại lỗi chi tiết để debug
            print(f"Lỗi nghiêm trọng trong StockDataAPIView: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({"error": f"Đã xảy ra lỗi không xác định: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)