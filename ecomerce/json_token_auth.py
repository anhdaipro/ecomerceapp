from django.db import close_old_connections
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from jwt import decode as jwt_decode
from django.conf import settings
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs
 
 
class TokenAuthMiddleware:
    """
    Custom token auth middleware
    """
 
    def __init__(self, inner):
        # Store the ASGI application we were passed
        self.inner = inner
 
    def __call__(self, scope):
 
        # Close old database connections to prevent usage of timed out connections
        close_old_connections()
        request=self.request
        # Get the token
        token = request.GET.get('token')
 
        # Try to authenticate the user
        try:
            # This will automatically validate the token and raise an error if token is invalid
            UntypedToken(token)
        except (InvalidToken, TokenError) as e:
            # Token is invalid
            print(e)
            return None
        else:
            #  Then token is valid, decode it
            user = request.user
 
        # Return the inner application directly and let it run everything else
        return self.inner(dict(scope, user=user))