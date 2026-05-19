"""
ASGI config for pizzeria_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from django.core.asgi import get_asgi_application

import devices.routing

import os


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pizzeria_backend.settings')


application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            devices.routing.websocket_urlpatterns
        )
    )
})
