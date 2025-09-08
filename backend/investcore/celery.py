import os
from celery import Celery

# Đặt biến môi trường mặc định cho Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'investcore.settings')

app = Celery('investcore')

# Sử dụng chuỗi config từ Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Tự động tìm các file tasks.py trong tất cả các app đã đăng ký
app.autodiscover_tasks()