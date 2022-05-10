from urllib import parse
from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import AccessToken
from django.contrib.auth.models import User
@database_sync_to_async
def get_user(**kwargs):
    try:
        return User.objects.get(**kwargs)
    except User.DoesNotExist:
        return AnonymousUser()

class JwtAuthMiddleware:

    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        return JwtAuthMiddlewareInstance(scope, self)

class JwtAuthMiddlewareInstance:
    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        try:
            token = self.request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
            token_decoded = AccessToken(token)
            
            scope['user'] = self.request.user
        except Exception:
            scope['user'] = AnonymousUser()
        return self.inner(scope)
    
        
JwtAuthMiddlewareStack = lambda inner: JwtAuthMiddleware(AuthMiddlewareStack(inner))