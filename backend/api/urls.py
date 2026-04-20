from django.urls import path, include
from .views import (RegisterAPIView,
                    StockDataAPIView,
                    StockDetailAPIView,
                    WatchlistListCreateView,
                    WatchlistDeleteView,
                    ArticleListAPIView,
                    StockScreenerAPIView,
                    StockSearchAPIView,
                    MLPredictionListAPIView,
                    MLPredictionDetailAPIView,
                    MarketStateAPIView,
                    AnomalyAlertListAPIView,
                    MLModelInfoAPIView,)
                    # ChatbotView)
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

router = DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),

    path('register/', RegisterAPIView.as_view(), name='register'),
    path('login/', obtain_auth_token, name='login'),

    path('stocks/search/', StockSearchAPIView.as_view(), name='stock-search'),

    path('stock-data/', StockDataAPIView.as_view(), name='stock-data'),
    path('stocks/<str:ticker>/', StockDetailAPIView.as_view(), name='stock-detail'),

    path('watchlist/', WatchlistListCreateView.as_view(), name='watchlist-list-create'),
    path('watchlist/<int:pk>/', WatchlistDeleteView.as_view(), name='watchlist-delete'),

    path('news/', ArticleListAPIView.as_view(), name='news-list'),

    path('screener/', StockScreenerAPIView.as_view(), name='stock-screener'),

    # ML Prediction endpoints
    path('ml/predictions/', MLPredictionListAPIView.as_view(), name='ml-prediction-list'),
    path('ml/predictions/<str:ticker>/', MLPredictionDetailAPIView.as_view(), name='ml-prediction-detail'),
    path('ml/market-state/', MarketStateAPIView.as_view(), name='ml-market-state'),
    path('ml/anomalies/', AnomalyAlertListAPIView.as_view(), name='ml-anomaly-list'),
    path('ml/model-info/', MLModelInfoAPIView.as_view(), name='ml-model-info'),

    # path('chat/', ChatbotView.as_view(), name='chatbot'),

]