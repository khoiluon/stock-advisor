from django.urls import path
from .views import RegisterAPIView
from rest_framework.authtoken.views import obtain_auth_token # View có sẵn của DRF để login

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('login/', obtain_auth_token, name='login'), # DRF cung cấp sẵn view này
]