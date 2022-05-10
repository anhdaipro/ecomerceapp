from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from jwt import decode as jwt_decode
from urllib.parse import parse_qs
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from django.conf import settings


@database_sync_to_async
def get_user(user_id):
    User = get_user_model()
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return 'AnonymousUser'


class TokenAuthMiddleware:

    def __init__(self, app):
        # Store the ASGI application we were passed
        self.app = app

    async def __call__(self, scope, receive, send):
        # Look up user from query string (you should also do things like
        # checking if it is a valid user ID, or if scope["user"] is already
        # populated).

        token = parse_qs(scope["query_string"].decode("utf8"))["token"][0]
        print(token)
        try:
            # This will automatically validate the token and raise an error if token is invalid
            is_valid = UntypedToken(token)
        except (InvalidToken, TokenError) as e:
            # Token is invalid
            print(e)
            return None
        else:
            #  Then token is valid, decode it
            decoded_data = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            print(decoded_data)

            scope['user'] = await get_user(int(decoded_data.get('user_id', None)))

            # Return the inner application directly and let it run everything else

        return await self.app(scope, receive, send) 