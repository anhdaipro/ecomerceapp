
from django.urls import path
from . import views
from .views import (ListThreadAPIView,ActionThread,CountThread,MediathreadAPI,CreateThread)

urlpatterns = [
    path('conversations/<int:id>',ActionThread.as_view()),
    path('thread/list', ListThreadAPIView.as_view()), 
    path('thread/new', CreateThread.as_view()), 
]