from django.urls import path
from . import consumers
websocket_urlpatterns = [
    path('', consumers.NotificationConsumer.as_asgi()),
    path('cart', consumers.NotificationConsumer.as_asgi()),
]