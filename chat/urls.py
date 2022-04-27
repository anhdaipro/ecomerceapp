
from django.urls import path
from . import views
from .views import (MessageAPIView,ThreadAPIView,ListThreadAPIView,ActionThread)

urlpatterns = [
    path('message', MessageAPIView.as_view()),
    path('chat', ThreadAPIView.as_view()),
    path('conversations/<int:id>',ActionThread.as_view()),
    path('thread/list', ListThreadAPIView.as_view()),
]