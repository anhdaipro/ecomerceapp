"""ecomerce URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include,re_path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.conf.urls import url
from django.views.static import serve
from rest_framework.authtoken.views import obtain_auth_token
from django.views.generic import TemplateView

urlpatterns = [
    path('admin', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('api-auth/', include('drf_social_oauth2.urls',namespace='drf')),
    path('password-reset',auth_views.PasswordResetView.as_view(
             template_name='account/password_reset.html'),name='password_reset'),
    path('password-reset/done',auth_views.PasswordResetDoneView.as_view(
             template_name='account/password_reset_done.html'),name='password_reset_done'),
    path('forgot_password/<uidb64>/<token>',auth_views.PasswordResetConfirmView.as_view(
             template_name='account/password_reset_confirm.html'
         ),name='password_reset_confirm'),
    path('password-reset-complete',auth_views.PasswordResetCompleteView.as_view(
             template_name='account/password_reset_complete.html'
         ),name='password_reset_complete'),
    path('<str:slug>',views.category, name='category'),
    path('bundle-deal/<int:id>',views.bundle_deal,name='promotion_combo'),
    path('addon-deal-cart-selection/<int:id>', views.deal_shock,name="deal_shock"),
    path('api/v4/',include('buyer.urls')),
    path('api/v1/', include("notification.urls")),
    path('api/v3/',include('seller.urls'))
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += [re_path(r'^.*', TemplateView.as_view(template_name='index.html'))]
