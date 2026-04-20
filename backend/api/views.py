# api/views.py
import re
from django.contrib.auth.models import User
from django.db.models import Q
from django.db.models.functions import Length
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
import pandas as pd
from rest_framework import permissions
from django.conf import settings
# import google.generativeai as genai
from .models import Stock, StockData, Watchlist, PotentialStock, Article, ChatSession, ChatMessage
from .models import MLStock, MLModel, MLPrediction, AnomalyAlert, MarketState
from .pagination import StandardResultsSetPagination
from .serializers import (
    RegisterSerializer, StockSerializer, WatchlistSerializer,
    ArticleSerializer, PotentialStockSerializer, StockDataSerializer, ChatSessionSerializer,
    MLPredictionSerializer, AnomalyAlertSerializer, MarketStateSerializer, MLModelInfoSerializer,
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

            # BƯỚC 4: Tính toán các chỉ báo kỹ thuật bằng pandas-ta-classic
            # Thư viện này tự động tìm các cột 'open', 'high', 'low', 'close', 'volume'
            # df.ta.macd(fast=12, slow=26, signal=9, append=True)
            # df.ta.rsi(length=14, append=True)
            # df.ta.bbands(length=20, std=2, append=True)
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


# class ChatbotView(APIView):
#     permission_classes = [permissions.IsAuthenticated]
#
#     def post(self, request):
#         user = request.user
#         user_message_content = request.data.get('message')
#         session_id = request.data.get('session_id')
#
#         if not user_message_content:
#             return Response({"error": "Message is required."}, status=status.HTTP_400_BAD_REQUEST)
#
#         chat_session = None
#         if session_id:
#             try:
#                 chat_session = ChatSession.objects.get(id=session_id, user=user)
#             except ChatSession.DoesNotExist:
#                 # Nếu không tìm thấy session, tạo một session mới
#                 chat_session = ChatSession.objects.create(user=user)
#         else:
#             chat_session = ChatSession.objects.create(user=user)
#
#         ChatMessage.objects.create(session=chat_session, sender='user', content=user_message_content)
#
#         try:
#             genai.configure(api_key='AIzaSyDN4BrwKCF0T7CwgZlD30KoOP9m2LTxweg')
#             client = genai.GenerativeModel('gemini-2.5-flash')
#
#             system_instruction = self.get_system_instruction(user_message_content)
#
#             full_history = [
#                 {'role': 'user', 'parts': [{'text': system_instruction}]},
#                 {'role': 'model',
#                  'parts': [{'text': "Tôi đã hiểu. Tôi là Trợ lý Phân tích Chứng khoán và sẵn sàng hỗ trợ."}]}
#             ]
#
#             # Lấy lịch sử trò chuyện từ DB và nối vào sau
#             conversation_history = ChatMessage.objects.filter(session=chat_session).order_by('timestamp')
#             for msg in conversation_history:
#                 role = 'user' if msg.sender == 'user' else 'model'
#                 full_history.append({'role': role, 'parts': [{'text': msg.content}]})
#
#             # Gọi API với cú pháp đúng
#             response = client.generate_content(
#                 contents=full_history  # Truyền toàn bộ lịch sử đã gộp
#             )
#             ai_response_content = response.text
#
#             ChatMessage.objects.create(session=chat_session, sender='ai', content=ai_response_content)
#
#             updated_session = ChatSession.objects.get(id=chat_session.id)
#             session_serializer = ChatSessionSerializer(updated_session)
#             return Response(session_serializer.data, status=status.HTTP_200_OK)
#
#         except Exception as e:
#             error_details = f"Lỗi từ Generative AI: {repr(e)}"
#             print(f"!!! LỖI NGOẠI LỆ TRONG CHATBOT VIEW: {error_details}")
#             return Response({"error": "Xin lỗi, đã có lỗi xảy ra phía máy chủ."},
#                             status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#     def get_system_instruction(self, user_message):
#         all_tickers = list(Stock.objects.values_list('ticker', flat=True))
#         mentioned_tickers = [ticker for ticker in all_tickers if
#                              re.search(r'\b' + re.escape(ticker) + r'\b', user_message.upper())]
#
#         context_data = ""
#         if mentioned_tickers:
#             ticker = mentioned_tickers[0]
#             context_data += f"\nDữ liệu ngữ cảnh cho mã {ticker}:\n"
#
#             latest_data = StockData.objects.filter(stock__ticker=ticker).order_by('-date').first()
#             if latest_data:
#                 context_data += f"- Giá đóng cửa gần nhất ({latest_data.date}): {latest_data.close}\n"
#
#             suggestion = PotentialStock.objects.filter(stock__ticker=ticker).order_by('-analysis_date').first()
#             if suggestion:
#                 context_data += f"- Gợi ý từ hệ thống ADMRS: {suggestion.reason} (Timeframe: {suggestion.timeframe}, Score: {suggestion.score}/10, Confidence: {suggestion.confidence}%)\n"
#
#         # === SỬA LỖI CÚ PHÁP: ĐẢM BẢO RETURN LÀ MỘT CHUỖI F-STRING HOÀN CHỈNH ===
#         return f"""
#         Bạn là một Trợ lý Phân tích Chứng khoán AI của hệ thống Stock Advisor.
#         Vai trò của bạn: Cung cấp thông tin, phân tích và trả lời các câu hỏi về cổ phiếu một cách khách quan, dựa trên dữ liệu.
#
#         QUY TẮC BẮT BUỘC:
#         1.  Chỉ trả lời các câu hỏi liên quan đến chứng khoán, tài chính, cổ phiếu. Nếu người dùng hỏi lạc đề, hãy lịch sự từ chối.
#         2.  Khi đưa ra thông tin, hãy dựa vào "Dữ liệu ngữ cảnh" được cung cấp dưới đây nếu có.
#         3.  Không bao giờ đưa ra lời khuyên "mua" hay "bán" một cách chắc chắn. Luôn sử dụng các cụm từ như "theo phân tích của hệ thống", "dữ liệu cho thấy", "bạn nên cân nhắc thêm các yếu tố khác".
#         4.  Giữ câu trả lời ngắn gọn, chuyên nghiệp và đi thẳng vào vấn đề.
#
#         {context_data}
#         """


# ==============================================================================
# ML PREDICTION VIEWS
# ==============================================================================

class MLPredictionListAPIView(generics.ListAPIView):
    """
    GET /api/ml/predictions/
    Latest predictions, filter by ?trend=UP&min_confidence=70&exchange=HOSE
    """
    serializer_class = MLPredictionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        latest_date = (
            MLPrediction.objects.order_by('-prediction_date')
            .values_list('prediction_date', flat=True)
            .first()
        )
        if not latest_date:
            return MLPrediction.objects.none()

        qs = MLPrediction.objects.filter(prediction_date=latest_date).select_related('stock')

        trend = self.request.query_params.get('trend')
        if trend:
            qs = qs.filter(trend_class=trend.upper())

        min_confidence = self.request.query_params.get('min_confidence')
        if min_confidence:
            try:
                qs = qs.filter(confidence_score__gte=int(min_confidence))
            except (ValueError, TypeError):
                pass

        exchange = self.request.query_params.get('exchange')
        if exchange:
            qs = qs.filter(stock__exchange=exchange.upper())

        return qs


class MLPredictionDetailAPIView(APIView):
    """
    GET /api/ml/predictions/<ticker>/
    Latest prediction detail cho 1 mã.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, ticker):
        obj = (
            MLPrediction.objects
            .filter(stock__ticker=ticker.upper())
            .select_related('stock')
            .order_by('-prediction_date')
            .first()
        )
        if obj is None:
            return Response(
                {"detail": "No prediction found for this ticker."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(MLPredictionSerializer(obj).data)


class MarketStateAPIView(APIView):
    """
    GET /api/ml/market-state/
    Current market state + 30-day history.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        days = request.query_params.get('days', 30)
        try:
            days = int(days)
        except (ValueError, TypeError):
            days = 30

        states = MarketState.objects.order_by('-date')[:days]
        current = states.first() if states.exists() else None

        return Response({
            'current': MarketStateSerializer(current).data if current else None,
            'history': MarketStateSerializer(states, many=True).data,
        })


class AnomalyAlertListAPIView(generics.ListAPIView):
    """
    GET /api/ml/anomalies/
    Latest anomaly alerts, filter by ?type=volume_spike&days=7
    """
    serializer_class = AnomalyAlertSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        qs = AnomalyAlert.objects.select_related('stock').order_by('-detected_at')

        anomaly_type = self.request.query_params.get('type')
        if anomaly_type:
            qs = qs.filter(anomaly_type=anomaly_type)

        days = self.request.query_params.get('days', 7)
        try:
            days = int(days)
        except (ValueError, TypeError):
            days = 7

        from django.utils import timezone as tz
        from datetime import timedelta
        qs = qs.filter(detected_at__gte=tz.now() - timedelta(days=days))

        return qs


class MLModelInfoAPIView(APIView):
    """
    GET /api/ml/model-info/
    Active model metadata & metrics.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        active_models = MLModel.objects.filter(is_active=True)
        return Response({
            'total_active_models': active_models.count(),
            'models': MLModelInfoSerializer(active_models, many=True).data,
        })