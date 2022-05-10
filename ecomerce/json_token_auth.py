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

    def __init__(self, scope, middleware):
        self.middleware = middleware
        self.scope = dict(scope)
        self.inner = self.middleware.inner

    async def __call__(self, receive, send):
        close_old_connections()

        if self.scope.get('user') and self.scope.get('user').is_active:
            inner = self.inner(dict(self.scope, user=self.scope.get('user')))
            return await inner(receive, send)

        query_string = self.scope["query_string"]
        if not query_string:
            inner = self.inner(dict(self.scope, user=AnonymousUser()))
            return await inner(receive, send)

        try:
            query_dict = parse.parse_qs(query_string)
        except:
            inner = self.inner(dict(self.scope, user=AnonymousUser()))
            return await inner(receive, send)

        if type(query_dict.get('token')) is not list or not len(query_dict.get('token')):
            inner = self.inner(dict(self.scope, user=AnonymousUser()))
            return await inner(receive, send)

        raw_token = query_dict['token'][0]
        if not raw_token:
            inner = self.inner(dict(self.scope, user=AnonymousUser()))
            return await inner(receive, send)

        try:
            token_decoded = AccessToken(raw_token)
        except:
            token_decoded = None

        if not token_decoded:
            inner = self.inner(dict(self.scope, user=AnonymousUser()))
            return await inner(receive, send)

        user = await self.get_user(validated_token=token_decoded, )
        inner = self.inner(dict(self.scope, user=user))
        return await inner(receive, send)

    async def get_user(self, validated_token):
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except Exception:
            return AnonymousUser()

        try:
            user = await get_user(**{api_settings.USER_ID_FIELD: user_id})
        except:
            return AnonymousUser()

        if not user.is_active:
            return AnonymousUser()

        return user


JwtAuthMiddlewareStack = lambda inner: JwtAuthMiddleware(AuthMiddlewareStack(inner))