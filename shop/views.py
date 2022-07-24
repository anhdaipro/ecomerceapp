from django.shortcuts import render
# Create your views here.
from django.contrib.auth import login
import itertools
import re
from django.db.models import F
from django.core.paginator import Paginator
from django.core.serializers import serialize
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from itemdetail.models import *
from django.shortcuts import render, redirect
from django.contrib import messages
from account.models import *
from shop.models import *
from shipping.models import *
from orderactions.models import *
from category.models import *
from orders.models import *
from discounts.models import *
from chats.models import *
from carts.models import *
from django.db.models import FloatField,IntegerField
from django.db.models import Max, Min, Count, Avg,Sum,F,Value as V
from django.contrib.auth import authenticate,login,logout
from django.core import serializers
import json
from django.db.models import  Q
from calendar import weekday, day_name
import random
from django.db.models import Case, When
from django.utils import timezone
from datetime import timedelta
import datetime
from rest_framework_simplejwt.tokens import AccessToken
from django.db.models.functions import Coalesce
from bulk_update.helper import bulk_update
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models.functions import ExtractYear, ExtractMonth,ExtractHour,ExtractHour,ExtractDay,TruncDay,TruncHour,TruncMonth
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.generics import (
    ListAPIView, RetrieveAPIView, CreateAPIView,
    UpdateAPIView, DestroyAPIView
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from .serializers import (VoucherSerializer,ComboSerializer,
ProgramSerializer,DealsockSerializer,FlashsaleSerializer)
from buyer.serializers import (OrdersellerSerializer,ItemSellerSerializer,
VariationSerializer,
VoucherSerializer,
VouchersellerSerializer,
ShopProgramSerializer,
ShopprogramSellerSerializer,
ByproductSellerSerializer,
BuywithsockdealSerializer,
BuywithsockdealSellerSerializer,
ComboSerializer,
CombosellerSerializer,
BuywithsockdealinfoSerializer,
FlashSaleSerializer,
ReviewshopSerializer,
FlashSaleSellerSerializer,
VariationsellerSerializer,
ItemproductSerializer,)
class ListvoucherAPI(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = VoucherSerializer
    def get_queryset(self):
        request = self.request
        user=request.user
        shop=Shop.objects.get(user=user)
        return Voucher.objects.filter(shop=shop).prefetch_related('products').prefetch_related('order_voucher')
