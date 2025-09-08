from rest_framework.generics import RetrieveAPIView
from django.contrib.auth.models import User
from .serializers import RegisterSerializer, StockSerializer, WatchlistSerializer, ArticleSerializer, PotentialStockSerializer
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
import pandas as pd
import pandas_ta as ta
from .models import Stock, StockData, Watchlist, PotentialStock, Article
from django.db.models import Q
from django.db.models.functions import Length
from .pagination import StandardResultsSetPagination

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
            # truy xuất dữ liệu từ database
            queryset = StockData.objects.filter(stock__ticker=ticker_symbol).order_by('date')

            if not queryset.exists():
                return Response(
                    {"error": f"Không tìm thấy dữ liệu cho mã {ticker_symbol} trong database."},
                    status=status.HTTP_404_NOT_FOUND)

            # chuyển queryset thành DataFrame của Pandas để tính toán
            df = pd.DataFrame(list(queryset.values('date', 'open', 'high', 'low', 'close', 'volume')))

            # Đổi tên cột để pandas_ta có thể nhận diện
            df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'},
                      inplace=True)

            ohlcv_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in ohlcv_columns:
                df[col] = df[col].astype(float)

            # Bước 3: Tính toán các chỉ báo kỹ thuật
            df.ta.macd(close='Close', fast=12, slow=26, signal=9, append=True)
            df.ta.rsi(close='Close', length=14, append=True)
            df.ta.sma(close='Close', length=20, append=True)
            df.ta.sma(close='Close', length=50, append=True)

            df.ta.bbands(close='Close', length=20, std=2, append=True)

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


class ArticleListAPIView(generics.ListAPIView):
    """
    API để lấy danh sách tin tức.
    - Hỗ trợ lấy tất cả tin tức mới nhất.
    - Hỗ trợ lọc tin tức theo mã cổ phiếu (VD: /api/news/?ticker=FPT).
    """
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """
        Ghi đè phương thức này để thêm logic lọc.
        """
        queryset = Article.objects.all()  # Bắt đầu với tất cả bài viết

        # Lấy tham số 'ticker' từ URL
        ticker = self.request.query_params.get('ticker', None)

        if ticker is not None:
            # Nếu có ticker, lọc các bài viết có liên quan đến mã đó
            queryset = queryset.filter(related_stocks__ticker=ticker.upper())

        return queryset


class StockScreenerAPIView(generics.ListAPIView):
    """
    API trả về danh sách các cổ phiếu tiềm năng đã được phân tích.
    Hỗ trợ lọc theo khung thời gian (timeframe).
    Ví dụ: /api/screener/?timeframe=Ngắn hạn
    """
    serializer_class = PotentialStockSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Lấy danh sách các cổ phiếu tiềm năng được phân tích gần nhất
        và áp dụng các bộ lọc từ URL.
        """
        # Đầu tiên, chỉ lấy kết quả của ngày phân tích mới nhất
        latest_date = PotentialStock.objects.order_by('-analysis_date').values_list('analysis_date', flat=True).first()
        if not latest_date:
            return PotentialStock.objects.none()  # Trả về rỗng nếu chưa có dữ liệu

        queryset = PotentialStock.objects.filter(analysis_date=latest_date)

        # Lấy tham số 'timeframe' từ URL
        timeframe = self.request.query_params.get('timeframe', None)
        if timeframe:
            # Nếu có, lọc queryset theo timeframe đó
            queryset = queryset.filter(timeframe=timeframe)

        return queryset

class StockSearchAPIView(generics.ListAPIView):
    serializer_class = StockSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        query = self.request.query_params.get('q', '').upper() # Chuyển query thành chữ hoa
        if not query:
            return Stock.objects.none()

        # === LOGIC TÌM KIẾM THÔNG MINH HƠN ===

        # Lớp 1: Tìm mã khớp chính xác
        exact_match = Stock.objects.filter(ticker__exact=query)

        # Lớp 2: Tìm các mã BẮT ĐẦU BẰNG query, loại bỏ mã đã khớp chính xác
        # và ưu tiên các mã ngắn hơn lên trước (VIB trước VIB123)
        starts_with_matches = Stock.objects.filter(
            ticker__startswith=query
        ).exclude(
            ticker__exact=query
        ).order_by(Length('ticker')) # Sắp xếp theo độ dài ticker

        # Lớp 3: Tìm theo tên công ty, loại bỏ các kết quả đã có ở trên
        company_name_matches = Stock.objects.filter(
            company_name__icontains=query
        ).exclude(
            ticker__exact=query
        ).exclude(
            ticker__startswith=query
        )

        # Kết hợp kết quả theo thứ tự ưu tiên
        # Dùng set để đảm bảo không có mã nào bị trùng lặp
        seen_tickers = set()
        combined_results = []

        for stock in list(exact_match) + list(starts_with_matches) + list(company_name_matches):
            if stock.ticker not in seen_tickers:
                combined_results.append(stock)
                seen_tickers.add(stock.ticker)

        # Giới hạn 10 kết quả cuối cùng
        return combined_results[:10]