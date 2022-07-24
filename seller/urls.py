from django.urls import path
from . import views
from .views import (DashboardBundleAPI,DashboardVoucherAPI,DashboardAddonAPI
,DashboardFlashsaleAPI,
DashboardDiscount,DataBundleAPI
DataVoucherAPI,
DataDiscountAPI,
DataFlashsaleAPI,
DataAddonAPI)
urlpatterns = [
    path("dashboard", views.my_dashboard),
    path("dashboard/voucher", DashboardVoucherAPI.as_view()),
    path("dashboard/addon", DashboardAddonAPI.as_view()),
    path('dashboard/bundle',DashboardBundleAPI.as_view()),
    path('dashboard/flash',DashboardFlashsaleAPI.as_view()),
    path('dashboard/discount',DashboardDiscountAPI.as_view()),
    path('data/bundle',DataBundleAPI.as_view()),
    path('data/voucher',DataVoucherAPI.as_view()),
    path('data/discount',DataDiscountAPI.as_view()),
    path('data/flash_sale',DataFlashsaleAPI.as_view()),
    path('data/addon',DataAddonAPI.as_view()),
]