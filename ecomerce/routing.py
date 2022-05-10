# mysite/routing.py
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import chat.routing
from .json_token_auth import JwtAuthMiddleware
application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': JwtAuthMiddleware(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
})