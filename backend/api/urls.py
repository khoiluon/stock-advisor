from django.urls import path
from .views import RegisterAPIView, StockDataAPIView, StockDetailAPIView, WatchlistListCreateView, WatchlistDeleteView

from rest_framework.authtoken.views import obtain_auth_token # View có sẵn của DRF để login

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('login/', obtain_auth_token, name='login'), # DRF cung cấp sẵn view này
    path('stock-data/', StockDataAPIView.as_view(), name='stock-data'),
    path('stocks/<str:ticker>/', StockDetailAPIView.as_view(), name='stock-detail'),
    path('watchlist/', WatchlistListCreateView.as_view(), name='watchlist-list-create'),
    path('watchlist/<int:pk>/', WatchlistDeleteView.as_view(), name='watchlist-delete'),
]