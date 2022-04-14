from django.urls import path
from . import consumers
websocket_urlpatterns = [
    path('', consumers.ChatConsumer.as_asgi()),
    path('<slug>', consumers.ChatConsumer.as_asgi()),
    path('cart', consumers.ChatConsumer.as_asgi()),
    path('user/account/', consumers.ChatConsumer.as_asgi()),
]