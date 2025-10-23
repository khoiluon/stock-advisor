# stockadvisor/asgi.py (thay 'stockadvisor' bằng tên project của bạn)

import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import ssi_integration.routing # Import file routing chúng ta sắp tạo

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stockadvisor.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            ssi_integration.routing.websocket_urlpatterns
        )
    ),
})