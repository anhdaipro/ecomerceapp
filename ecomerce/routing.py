# mysite/routing.py
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import chat.routing
from token_auth import TokenAuthMiddleware
application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': TokenAuthMiddleware(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
})