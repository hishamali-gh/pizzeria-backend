import os

import devices.routing

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from django.core.asgi import get_asgi_application


# Tell 'Daphne' where exactly 'settings.py' lives.
""" 'setdefault()' method is used as a failsafe instead of direct assignment because, in production environments,
a cloud system administrator might want to override your default configurations to use a production setup file instead """

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pizzeria_backend.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(devices.routing.websocket_urlpatterns)
    )
})
