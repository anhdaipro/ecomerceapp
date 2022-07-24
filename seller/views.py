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
from buyer.serializers import (
FlashSaleSerializer,
ReviewshopSerializer,
FlashSaleSellerSerializer,
VariationsellerSerializer,
ItemproductSerializer,)

def datapromotion(shop,week,choice,orders,orders_last):
    data={}
    orders=orders.filter(ordered_date__date__gte=week)
    orders_last=orders_last.filter(Q(ordered_date__date__lt=week)&Q(ordered_date__date__gte=(week - timedelta(days=7))))
    
    if choice=='voucher':
        vouchers=Voucheruser.objects.filter(voucher__shop=shop)
        orders=orders.exclude(voucher=None)
        orders_last=orders_last.exclude(voucher=None)
        vouchers_user=vouchers.filter(created__date__gte=week)
        vouchers_last_user=vouchers.filter(Q(created__date__lt=week)&Q(created__date__gte=(week - timedelta(days=7))))
        count_use_voucher=orders.count()
        count_use_voucher_last=orders_last.count()
        count_voucher_received=vouchers_user.count()
        count_voucher_received_last=vouchers_user_last.count()
        usage_rate=count_use_voucher/count_voucher_received
        usage_rate_last=count_use_voucher_last/count_voucher_received_last
        data.update({'usage_rate':usage_rate,'usage_rate_last':usage_rate_last})
    else:
        cartitem=CartItem.objects.filter(shop=shop,ordered=True)
        cartitems=cartitem
        cartitems_last=cartitem
        if choice=='addon':
            orders=orders.filter(items__deal_shock__isnull=False).distinct()
            orders_last=orders_last.filter(items__deal_shock__isnull=False).distinct()
            cartitems=cartitems.exclude(deal_shock=None)
            cartitems_last=cartitems_last.exclude(deal_shock=None)
            amount_main=cartitems.aggregate(sum=Coalesce(Sum('amount_main_products'),0.0))
            amount_main_last=cartitems_last.aggregate(sum=Coalesce(Sum('amount_main_products'),0.0))
            amount_byproducts=cartitems.aggregate(sum=Coalesce(Sum('amount_byproducts'),0.0))
            amount_byproducts_last=cartitems_last.aggregate(sum=Coalesce(Sum('amount_byproducts'),0.0))
            quantity_byproducts=cartitems.aggregate(sum=Coalesce(Sum('byproduct_cart__quantity'),0))
            quantity_byproducts_last=cartitems_last.aggregate(sum=Coalesce(Sum('byproduct_cart__quantity'),0))
            data.update({'amount_main':amount_main['sum'],
                'amount_byproducts':amount_byproducts['sum'],
                'amount_main_last':amount_main_last['sum'],
                'amount_byproducts_last':amount_byproducts_last['sum']})
        if choice=='bundle':
            orders=orders.filter(items__promotion_combo__isnull=False).distinct()
            orders_last=orders_last.filter(items__promotion_combo__isnull=False).distinct()
            cartitems=cartitems.exclude(promotion_combo=None)
            cartitems_last=cartitems_last.exclude(promotion_combo=None)
        if choice=='flashsale':
            orders=orders.exclude(items__flash_sale__isnull=False)
            orders_last=orders_last.filter(items__flash_sale__isnull=False)
            cartitems=cartitems.exclude(flash_sale=None)
            cartitems_last=cartitems_last.exclude(flash_sale=None)
        if choice=='discount':
            orders=orders.filter(items__program__isnull=False)
            orders_last=orders_last.filter(items__program__isnull=False)
            cartitems=cartitems.exclude(program=None)
            cartitems_last=cartitems_last.exclude(program=None)
        cartitems=cartitems.filter(order_cartitem__in=orders)
        cartitems_last=cartitems_last.filter(order_cartitem__in=orders_last)
        total_quantity=cartitems.aggregate(sum=Coalesce(Sum('quantity'),0))
        total_quantity_last=cartitems_last.aggregate(sum=Coalesce(Sum('quantity'),0))
        data.update({'total_quantity':total_quantity['sum'],
        'total_quantity_last':total_quantity_last['sum'],})
   
    number_buyer=orders.order_by('user').distinct('user').count()
    total_amount=orders.aggregate(sum=Coalesce(Sum('amount'),0.0))
    total_order=orders.aggregate(count=Count('id'))
    number_buyer_last=orders_last.order_by('user').distinct('user').count()
    total_amount_last=orders_last.aggregate(sum=Coalesce(Sum('amount'),0.0))
    total_order_last=orders_last.aggregate(count=Count('id'))
    return{**data,'number_buyer':number_buyer,
        'total_amount':total_amount['sum'],'total_order_last':total_order_last['count'],
        'number_buyer_last':number_buyer_last,
        'total_amount_last':total_amount_last['sum'],
        'total_order':total_order['count']}
class DataVoucherAPI(APIView):
    def get(self,request):
        current_date=datetime.datetime.now()
        week=current_date-timedelta(days=7)
        shop=Shop.objects.get(user=request.user)
        orders=Order.objects.filter(shop=shop,accepted=True)
        choice='voucher'
        orders_last=orders
        datapromotion(shop,week,choice,orders,orders_last)
        return Response(datapromotion(shop,week,choice,orders,orders_last))
class DataAddonAPI(APIView):
    def get(self,request):
        current_date=datetime.datetime.now()
        week=current_date-timedelta(days=7)
        shop=Shop.objects.get(user=request.user)
        orders=Order.objects.filter(shop=shop,accepted=True)
        orders_last=orders
        choice='addon'
        datapromotion(shop,week,choice,orders,orders_last)
        return Response(datapromotion(shop,week,choice,orders,orders_last))
class DataBundleAPI(APIView):
    def get(self,request):
        current_date=datetime.datetime.now()
        week=current_date-timedelta(days=7)
        shop=Shop.objects.get(user=request.user)
        orders=Order.objects.filter(shop=shop,accepted=True)
        orders_last=orders
        choice='bundle'
        datapromotion(shop,week,choice,orders,orders_last)
        return Response(datapromotion(shop,week,choice,orders,orders_last))
class DataFlashsaleAPI(APIView):
    def get(self,request):
        current_date=datetime.datetime.now()
        week=current_date-timedelta(days=7)
        shop=Shop.objects.get(user=request.user)
        orders=Order.objects.filter(shop=shop,accepted=True)
        orders_last=orders
        choice='flashsale'
        datapromotion(shop,week,choice,orders,orders_last)
        return Response(datapromotion(shop,week,choice,orders,orders_last))
class DataDiscountAPI(APIView):
    def get(self,request):
        current_date=datetime.datetime.now()
        week=current_date-timedelta(days=7)
        shop=Shop.objects.get(user=request.user)
        orders=Order.objects.filter(shop=shop,accepted=True)
        orders_last=orders
        choice='discount'
        datapromotion(shop,week,choice,orders,orders_last)
        return Response(datapromotion(shop,week,choice,orders,orders_last))
import calendar
import pandas as pd

def dashboard(shop,time,time_choice,choice,orders,orders_last,current_date,yesterday,week,month):
        data={}
        cartitems=CartItem.objects.filter(order_cartitem__in=orders)
        cartitems_last=cartitems
        times = [i for i in range(24)]
        if time=='currentday':
            orders=orders.filter(ordered_date__date__gte=current_date).annotate(day=TruncHour('ordered_date'))
            orders_last=orders_last.filter(ordered_date__date=(current_date - timedelta(days=1)))
        if time=='day':
            day=pd.to_datetime(time_choice)
            order=orders.filter(ordered_date__date=day).annotate(day=TruncHour('ordered_date'))
            orders_last=orders_last.filter(Q(ordered_date__date=(day - timedelta(days=1))))
        if time=='yesterday':
            orders=orders.filter(ordered_date__date=yesterday).annotate(day=TruncHour('ordered_date'))
            orders_last=orders_last.filter(Q(ordered_date__date=(yesterday - timedelta(days=1))))
        if time=='week_before':
            times=[int((yesterday - datetime.timedelta(days=i)).date().strftime('%d')) for i in range(7)]
            orders=orders.filter(ordered_date__date__gte=week,ordered_date__date__lte=yesterday).annotate(day=TruncDay('ordered_date'))
            orders_last=orders_last.filter(Q(ordered_date__date__lt=week)&Q(ordered_date__date__gte=(week - timedelta(days=7))))
        if time=='week': 
            week=pd.to_datetime(time_choice)
            day_first_week=week - datetime.timedelta(days=week.isoweekday() % 7)
            day_weeks=[int((day_first_week + datetime.timedelta(days=i)).date().strftime('%d')) for i in range(7)]
            orders=Order.objects.filter(ordered_date__week=week.isocalendar()[1],ordered_date__year=week.year).annotate(day=TruncDay('ordered_date'))
            orders_last=orders_last.filter(Q(ordered_date__week=(week.isocalendar()[1] - 1)))
        if time=='month': 
            month=pd.to_datetime(time_choice)
            day_last_month = pd.Period(month,freq='M').end_time.date() 
            times=[int((day_last_month-datetime.timedelta(days=i)).strftime('%d')) for i in range(int(day_last_month.strftime('%d')))]
            orders=orders.filter(ordered_date__month=month.month,ordered_date__year=month.year).annotate(day=TruncDay('ordered_date'))
            orders_last=orders_last.filter(Q(ordered_date__month=(month.month - 1)))
        if time=='month_before':
            times=[int((yesterday-datetime.timedelta(days=i)).date().strftime('%d')) for i in range(30)]
            orders=orders.filter(ordered_date__date__gte=month,ordered_date__date__lte=yesterday).annotate(day=TruncDay('ordered_date'))
            orders_last=list_order_last.filter(Q(ordered_date__date__lt=month)&Q(ordered_date__date__gte=(month - timedelta(days=30)))) 
        if time=='year':
            times=[i for i in range(1,13)]
            year=pd.to_datetime(time_choice)
            orders=orders.filter(ordered_date__year=year.year).annotate(day=TruncMonth('ordered_date'))
            orders_last=orders_last.filter(Q(ordered_date__year=(year.year - 1)))

        if choice=='voucher':
            orders=orders.exclude(voucher=None)
            orders_last=orders_last.exclude(voucher=None)
            count_use_voucher=orders.count()
            count_use_voucher_last=orders_last.count()
            discount_voucher=orders.aggregate(sum=Coalesce(Sum('discount_voucher'),0.0))
            discount_voucher_last=orders_last.aggregate(sum=Coalesce(Sum('discount_voucher'),0.0))
            data.update({'count_use_voucher':count_use_voucher,
            'count_use_voucher_last':count_use_voucher_last,
            'discount_voucher_last':discount_voucher_last['sum'],
            'discount_voucher':discount_voucher['sum']})
        if choice=='addon':
            orders=orders.filter(items__deal_shock__isnull=False).distinct()
            orders_last=orders_last.filter(items__deal_shock__isnull=False).distinct()
            cartitems=cartitems.exclude(deal_shock=None)
            cartitems_last=cartitems_last.exclude(deal_shock=None)
            amount_main=cartitems.aggregate(sum=Coalesce(Sum('amount_main_products'),0.0))
            amount_main_last=cartitems_last.aggregate(sum=Coalesce(Sum('amount_main_products'),0.0))
            amount_byproducts=cartitems.aggregate(sum=Coalesce(Sum('amount_byproducts'),0.0))
            amount_byproducts_last=cartitems_last.aggregate(sum=Coalesce(Sum('amount_byproducts'),0.0))
            quantity_byproducts=cartitems.aggregate(sum=Coalesce(Sum('byproduct_cart__quantity'),0))
            quantity_byproducts_last=cartitems_last.aggregate(sum=Coalesce(Sum('byproduct_cart__quantity'),0))
            data.update({'amount_main':amount_main['sum'],'amount_byproducts':amount_byproducts['sum'],
                'amount_main_last':amount_main_last['sum'],
                'amount_byproducts_last':amount_byproducts_last['sum'],
                'quantity_byproducts':quantity_byproducts['sum'],
                'quantity_byproducts_last':quantity_byproducts_last['sum']})
        if choice=='bundle':
            orders=orders.filter(items__promotion_combo__isnull=False).distinct()
            orders_last=orders_last.filter(items__promotion_combo__isnull=False).distinct()
            cartitems=cartitems.exclude(promotion_combo=None)
            cartitems_last=cartitems_last.exclude(promotion_combo=None)
            count_combo=cartitems.aggregate(count_promotion_order=Coalesce(Sum((F('quantity')/F('promotion_combo__quantity_to_reduced')),output_field=IntegerField()),0))
            count_combo_last=cartitems_last.aggregate(count_promotion_order=Coalesce(Sum((F('quantity')/F('promotion_combo__quantity_to_reduced')),output_field=IntegerField()),0))
            data.update({'count_combo':count_combo['count_promotion_order'],
            'count_combo_last':count_combo_last['count_promotion_order']})
        if choice=='flashsale':
            orders=orders.exclude(items__flash_sale__isnull=False)
            orders_last=orders_last.filter(items__flash_sale__isnull=False)
            cartitems=cartitems.exclude(flash_sale=None)
            cartitems_last=cartitems_last.exclude(flash_sale=None)
        if choice=='discount':
            orders=orders.filter(items__program__isnull=False)
            orders_last=orders_last.filter(items__program__isnull=False)
            cartitems=cartitems.exclude(program=None)
            cartitems_last=cartitems_last.exclude(program=None)
        cartitems=cartitems.filter(order_cartitem__in=orders)
        cartitems_last=cartitems_last.filter(order_cartitem__in=orders_last)
        list_total_order=orders.values('day').annotate(count=Count('id')).values('day','count')
        list_total_amount=orders.values('day').annotate(sum=Coalesce(Sum('amount'),0.0)).values('day','sum')
        total_quantity=cartitems.aggregate(sum=Coalesce(Sum('quantity'),0))
        number_buyer=orders.order_by('user').distinct('user').count()
        total_amount=orders.aggregate(sum=Coalesce(Sum('amount'),0.0))
        total_order=orders.aggregate(count=Count('id'))
        total_quantity_last=cartitems_last.aggregate(sum=Coalesce(Sum('quantity'),0))
        number_buyer_last=orders_last.order_by('user').distinct('user').count()
        total_amount_last=orders_last.aggregate(sum=Coalesce(Sum('amount'),0.0))
        total_order_last=orders_last.aggregate(count=Count('id'))
        return {'number_buyer':number_buyer,**data,'times':times,
        'total_amount':total_amount['sum'],'total_order_last':total_order_last['count'],
        'total_quantity':total_quantity['sum'],
        'total_quantity_last':total_quantity_last['sum'],
        'number_buyer_last':number_buyer_last,
        'total_amount_last':total_amount_last['sum'],'total_order':total_order['count'],
        'count':list(list_total_order),'sum':list(list_total_amount)}
        
class DashboardDiscountAPI(APIView):
    def get(self,request):
        current_date=datetime.datetime.now()
        yesterday=current_date-timedelta(days=1)
        week=current_date-timedelta(days=7)
        month=current_date-timedelta(days=30)
        time=request.GET.get('time')
        choice='discount'
        time_choice=request.GET.get('time_choice')
        shop=Shop.objects.get(user=request.user)
        orders=Order.objects.filter(shop=shop,accepted=True)
        orders_last=orders
        dashboard(shop,time,time_choice,choice,orders,orders_last,current_date,yesterday,week,month)
        return Response(dashboard(shop,time,time_choice,choice,orders,orders_last,current_date,yesterday,week,month))

class DashboardAddonAPI(APIView):
    def get(self,request):
        current_date=datetime.datetime.now()
        yesterday=current_date-timedelta(days=1)
        week=current_date-timedelta(days=7)
        month=current_date-timedelta(days=30)
        time=request.GET.get('time')
        choice='addon'
        time_choice=request.GET.get('time_choice')
        shop=Shop.objects.get(user=request.user)
        orders=Order.objects.filter(shop=shop,accepted=True)
        orders_last=orders
        dashboard(shop,time,time_choice,choice,orders,orders_last,current_date,yesterday,week,month)
        return Response(dashboard(shop,time,time_choice,choice,orders,orders_last,current_date,yesterday,week,month))
class DashboardVoucherAPI(APIView):
    def get(self,request):
        current_date=datetime.datetime.now()
        yesterday=current_date-timedelta(days=1)
        week=current_date-timedelta(days=7)
        month=current_date-timedelta(days=30)
        time=request.GET.get('time')
        choice='voucher'
        time_choice=request.GET.get('time_choice')
        shop=Shop.objects.get(user=request.user)
        orders=Order.objects.filter(shop=shop,accepted=True)
        orders_last=orders
        dashboard(shop,time,time_choice,choice,orders,orders_last,current_date,yesterday,week,month)
        vouchers=Voucheruser.objects.filter(voucher__shop=shop)
        vouchers_user=vouchers
        vouchers_last_user=vouchers
        if time=='currentday':
            vouchers_user=vouchers_user.filter(created__date__gte=current_date)
            vouchers_last_user=vouchers_last_user.filter(created__date=(current_date - timedelta(days=1))) 
        if time=='day':
            day=pd.to_datetime(time_choice)
            order=orders.filter(created__date=day)
            vouchers_last_user=vouchers_last_user.filter(Q(created__date=(day - timedelta(days=1))))
        if time=='yesterday':
            vouchers_user=vouchers_user.filter(created__date=yesterday)
            vouchers_last_user=vouchers_last_user.filter(Q(created__date=(yesterday - timedelta(days=1))))
        if time=='week_before':
            vouchers_user=vouchers_user.filter(created__date__gte=week,created__date__lte=yesterday)
            vouchers_last_user=vouchers_last_user.filter(Q(created__date__lt=week)&Q(created__date__gte=(week - timedelta(days=7))))
        if time=='week':  
            week=pd.to_datetime(time_choice)
            orders=Order.objects.filter(created__week=week.isocalendar()[1],created__year=week.year)
            vouchers_last_user=vouchers_last_user.filter(Q(created__week=(week.isocalendar()[1] - 1)))
        if time=='month': 
            month=pd.to_datetime(time_choice)
            vouchers_user=vouchers_user.filter(created__month=month.month,created__year=month.year)
            vouchers_last_user=vouchers_last_user.filter(Q(created__month=(month.month - 1)))
        if time=='month_before':
            vouchers_user=vouchers_user.filter(created__date__gte=month,created__date__lte=yesterday)
            vouchers_user_last=vouchers_user_last.filter(Q(created__date__lt=month)&Q(created__date__gte=(month - timedelta(days=30)))) 
        data={'count_voucher_received':vouchers_user.count(),'count_voucher_received_last':vouchers_user_last.count()}
        datachart={**data,**dashboard(shop,time,time_choice,choice,orders,orders_last,current_date,yesterday,week,month)}
        return Response(datachart)
class DashboardFlashsaleAPI(APIView):
    def get(self,request):
        shop=Shop.objects.get(user=request.user)
        current_date=datetime.datetime.now()
        yesterday=current_date-timedelta(days=1)
        week=current_date-timedelta(days=7)
        month=current_date-timedelta(days=30)
        time=request.GET.get('time')
        choice='flashsale'
        time_choice=request.GET.get('time_choice')
        orders=Order.objects.filter(shop=shop,accepted=True)
        orders_last=orders
        dashboard(shop,time,time_choice,choice,orders,orders_last,current_date,yesterday,week,month)
        return Response(dashboard(shop,time,time_choice,choice,orders,orders_last,current_date,yesterday,week,month))
class DashboardBundleAPI(APIView):
    def get(self,request):
        shop=Shop.objects.get(user=request.user)
        current_date=datetime.datetime.now()
        yesterday=current_date-timedelta(days=1)
        week=current_date-timedelta(days=7)
        month=current_date-timedelta(days=30)
        time=request.GET.get('time')
        choice='bundle'
        time_choice=request.GET.get('time_choice')
        orders=Order.objects.filter(shop=shop,accepted=True)
        orders_last=orders
        dashboard(shop,time,time_choice,choice,orders,orders_last,current_date,yesterday,week,month)
        return Response(dashboard(shop,time,time_choice,choice,orders,orders_last,current_date,yesterday,week,month))

@api_view(['GET', 'POST'])
def my_dashboard(request):
        user=request.user
        shop=Shop.objects.get(user=user)
        current_date=datetime.datetime.now()
        start_date=datetime.datetime.now()-timedelta(days=1)
        yesterday=current_date-timedelta(days=1)
        week=current_date-timedelta(days=7)
        last_weeks=current_date-timedelta(days=14)
        month=current_date-timedelta(days=30)
        time=request.GET.get('time')
        time_choice=request.GET.get('time_choice')
        typeorder=request.GET.get('typeorder')
        canceled=False
        if typeorder=='canceled':
            canceled=True
        accepted=[False,True]
        ordered=True
        if typeorder=='accepted':
            accepted=[True]
        received=[False,True]
        if typeorder=='receive':
            received=[True]
        total_order=Order.objects.filter(shop=shop,ordered_date__date=current_date).annotate(day=TruncHour('ordered_date')).values('day').annotate(count=Count('id')).values('day','count')
        total_amount=Order.objects.filter(shop=shop,ordered_date__date=current_date).annotate(day=TruncHour('ordered_date')).values('day').annotate(sum=Sum('amount')).values('day','sum')
        result =Order.objects.filter(shop=shop,ordered=True).aggregate(
            order=Count('id', filter=Q(ordered_date__date=current_date)),
            order_last=Count('id', filter=Q(ordered_date__date=(current_date - timedelta(days=1)))),
            amount=Coalesce(Sum('amount', filter=Q(ordered_date__date=current_date),output_field=FloatField()),0.0),
            amount_last=Coalesce(Sum('amount', filter=Q(ordered_date__date=(current_date - timedelta(days=1)))),0.0),  
        )
        
        #--------------------------day-------------------------------
        if time:
            if time=='current_day' or time=='day' or time=='yesterday':
                total_amount_days=[]
                total_order_days=[]
                hour_number=[]
                hour = [i for i in range(24)]
                sum_hour=[0 for i in range(current_date.hour+1)]
                count_hour=[0 for i in range(current_date.hour+1)]
                total_order_day=Order.objects.filter(shop=shop,ordered_date__date__gte=current_date,ordered=ordered,accepted__in=accepted,canceled=canceled,received__in=received).annotate(day=TruncHour('ordered_date')).values('day').annotate(count=Count('id')).values('day','count')
                total_amount_day=Order.objects.filter(shop=shop,ordered_date__date__gte=current_date,ordered=ordered,accepted__in=accepted,canceled=canceled,received__in=received).annotate(day=TruncHour('ordered_date')).values('day').annotate(sum=Sum('amount')).values('day','sum')
                result =Order.objects.filter(shop=shop,ordered=ordered,accepted__in=accepted,canceled=canceled,received__in=received).aggregate(
                    order=Count('id', filter=Q(ordered_date__date=current_date)),
                    order_last=Count('id', filter=Q(ordered_date__date=(current_date - timedelta(days=1)))),
                    amount=Coalesce(Sum('amount', filter=Q(ordered_date__date=current_date),output_field=FloatField()),0.0),
                    amount_last=Coalesce(Sum('amount', filter=Q(ordered_date__date=(current_date - timedelta(days=1)))),0.0),
                )

                if time=='yesterday':
                    otal_order_day=Order.objects.filter(shop=shop,ordered_date__date=yesterday,ordered=ordered,accepted__in=accepted,canceled=canceled,received__in=received).annotate(day=TruncHour('ordered_date')).values('day').annotate(count=Count('id')).values('day','count')
                    total_amount_day=Order.objects.filter(shop=shop,ordered_date__date=yesterday,ordered=ordered,accepted__in=accepted,canceled=canceled,received__in=received).annotate(day=TruncHour('ordered_date')).values('day').annotate(sum=Sum('amount')).values('day','sum')
                    result =Order.objects.filter(shop=shop,ordered=ordered,accepted__in=accepted,canceled=canceled,received__in=received).aggregate(
                    order=Count('id', filter=Q(ordered_date__date=yesterday)),
                    order_last=Count('id', filter=Q(ordered_date__date=(yesterday - timedelta(days=1)))),
                    amount=Coalesce(Sum('amount', filter=Q(ordered_date__date=yesterday)),0.0),
                    amount_last=Coalesce(Sum('amount', filter=Q(ordered_date__date=(yesterday - timedelta(days=1)))),0.0),
                    )
                    sum_hour=[0 for i in range(24)]
                    count_hour=[0 for i in range(24)]
                    
                elif time=='day':
                    day=pd.to_datetime(time_choice)
                    total_order=Order.objects.filter(shop=shop,ordered_date__date=day,ordered=ordered,accepted__in=accepted,canceled=canceled,received__in=received).annotate(day=TruncHour('ordered_date')).values('day').annotate(count=Count('id')).values('day','count')
                    total_amount=Order.objects.filter(shop=shop,ordered_date__date=day,ordered=ordered,accepted__in=accepted,canceled=canceled,received__in=received).annotate(day=TruncHour('ordered_date')).values('day').annotate(sum=Sum('amount')).values('day','sum')
                    result =Order.objects.filter(shop=shop,ordered=ordered,accepted__in=accepted,canceled=canceled,received__in=received).aggregate(
                    order=Count('id', filter=Q(ordered_date__date=day)),
                    order_last=Count('id', filter=Q(ordered_date__date=(day - timedelta(days=1)))),
                    amount=Coalesce(Sum('amount', filter=Q(ordered_date__date=day)),0.0),
                    amount_last=Coalesce(Sum('amount', filter=Q(ordered_date__date=(day - timedelta(days=1)))),0.0),
                    )
                    sum_hour=[0 for i in range(24)]
                    count_hour=[0 for i in range(24)]
                for i in total_amount:
                    total_amount_days.append(round(i['sum'],1))
                    hour_number.append(i['day'].strftime("%I %p"))
                    for j in hour:
                        if i['day'].strftime("%I %p") ==datetime.time(j).strftime('%I %p'):
                            hour[j]=int(i['day'].strftime("%H"))
                            sum_hour[j]=round((i['sum']),1)
            
                for i in total_order:
                    total_order_days.append(i['count'])
                    hour_number.append(i['day'].strftime("%I %p"))
                    for j in hour:
                        if i['day'].strftime("%I %p") ==datetime.time(j).strftime('%I %p'):
                            hour[j]=int(i['day'].strftime("%H"))
                            count_hour[j]=int(i['count'])
                hours=[datetime.time(i).strftime('%H:00') for i in hour] 

                data={
                    'result':result,
                    'total_amount':total_amount_days,'total_order':total_order_days,
                    'time':hours,'sum':sum_hour,'count':count_hour
                    }
                return Response(data)
                
            #-----------------------------------day-----------------------------------------

            #----------------------------------week---------------------------------

            elif time=='week_before' or time=='week':
                total_amount_weeks=[]
                total_order_weeks=[]
                day_week=[]
                day_weeks=[int((start_date - datetime.timedelta(days=i)).date().strftime('%d')) for i in range(7)]
                
                sum_day_week=[0 for i in range(7)]
                count_day_week=[0 for i in range(7)]
                total_order=Order.objects.filter(shop=shop,ordered_date__date__gte=week,ordered_date__date__lte=start_date,ordered=ordered,accepted__in=accepted,canceled=canceled,received__in=received).annotate(day=TruncDay('ordered_date')).values('day').annotate(count=Count('id')).values('day','count')
                total_amount=Order.objects.filter(shop=shop,ordered_date__date__gte=week,ordered_date__date__lte=start_date,ordered=ordered,accepted__in=accepted,canceled=canceled,received__in=received).annotate(day=TruncDay('ordered_date')).values('day').annotate(sum=Sum('amount')).values('day','sum')
                result =Order.objects.filter(shop=shop,ordered=ordered,accepted__in=accepted,canceled=canceled,received__in=received).aggregate(
                    order=Count('id', filter=Q(ordered_date__date__gt=week)),
                    order_last=Count('id', filter=(Q(ordered_date__date__lt=week)&Q(ordered_date__date__gte=(week - timedelta(days=7))))),
                    amount=Coalesce(Sum('amount', filter=Q(ordered_date__date__gte=week)),0.0),
                    amount_last=Coalesce(Sum('amount', filter=(Q(ordered_date__date__lt=week)&Q(ordered_date__date__gte=(week - timedelta(days=7))))),0.0),
                    )
                if time=='week':
                    week=pd.to_datetime(time_choice)
                    total_order=Order.objects.filter(shop=shop,ordered_date__week=week.isocalendar()[1],ordered_date__year=week.year,ordered=ordered,accepted__in=accepted,canceled=canceled,received__in=received).annotate(day=TruncDay('ordered_date')).values('day').annotate(count=Count('id')).values('day','count')
                    total_amount=Order.objects.filter(shop=shop,ordered_date__week=week.isocalendar()[1],ordered_date__year=week.year,ordered=ordered,accepted__in=accepted,canceled=canceled,received__in=received).annotate(day=TruncDay('ordered_date')).values('day').annotate(sum=Sum('amount')).values('day','sum')
                    result =Order.objects.filter(shop=shop,ordered=ordered,accepted__in=accepted,canceled=canceled,received__in=received).aggregate(
                    order=Count('id', filter=Q(ordered_date__week=week.isocalendar()[1])),
                    order_last=Count('id', filter=Q(ordered_date__week=(week.isocalendar()[1] - 1))),
                    amount=Coalesce(Sum('amount', filter=Q(ordered_date__week=week.isocalendar()[1])),0.0),
                    amount_last=Coalesce(Sum('amount', filter=Q(ordered_date__week=(week.isocalendar()[1] - 1))),0.0),
                    
                    )
                    day_first_week=week - datetime.timedelta(days=week.isoweekday() % 7)
                    day_weeks=[int((day_first_week + datetime.timedelta(days=i)).date().strftime('%d')) for i in range(7)]
                day_weeks.sort()
                for i in total_amount:
                    total_amount_weeks.append(i['sum'])
                    day_week.append(i['day'].strftime("%d"))
                    for j in range(len(day_weeks)):
                        if int(i['day'].strftime("%d")) ==day_weeks[j]:
                            day_weeks[j]=int(i['day'].strftime("%d"))
                            sum_day_week[j]=int(i['sum'])

                for i in total_order:
                    total_order_weeks.append(i['count'])
                    day_week.append(i['day'].strftime("%d"))
                    for j in range(len(day_weeks)):
                        if int(i['day'].strftime("%d")) ==day_weeks[j]:
                            day_weeks[j]=i['day'].strftime("%d")
                            count_day_week[j]=int(i['count'])
                data={
                
                    'result':result,
                    'total_amount':total_amount_weeks,'total_order':total_order_weeks,
                    'time':day_weeks,'sum':sum_day_week,'count':count_day_week, 
                    
                    }       
                return Response(data)  

            #--------------------------------week-------------------------------------------
            #------------------------------month-------------------------------------------

            elif time=='month' or time=='month_before':
                total_amount_months=[]
                total_order_months=[]
                day_month=[]
                day_months=[int((start_date-datetime.timedelta(days=i)).date().strftime('%d')) for i in range(30)]
                total_order=Order.objects.filter(shop=shop,ordered_date__date__gte=month,ordered_date__date__lte=start_date,ordered=ordered,accepted__in=accepted,canceled=canceled,received__in=received).annotate(day=TruncDay('ordered_date')).values('day').annotate(count=Count('id')).values('day','count')
                total_amount=Order.objects.filter(shop=shop,ordered_date__date__gte=month,ordered_date__date__lte=start_date,ordered=ordered,accepted__in=accepted,canceled=canceled,received__in=received).annotate(day=TruncDay('ordered_date')).values('day').annotate(sum=Sum('amount')).values('day','sum')
                result =Order.objects.filter(shop=shop,ordered=ordered,accepted__in=accepted,canceled=canceled,received__in=received).aggregate(
                    order=Count('id', filter=Q(ordered_date__date__gt=month)),
                    order_last=Count('id', filter=(Q(ordered_date__date__lt=month)&Q(ordered_date__date__gte=(month - timedelta(days=30))))),
                    amount=Coalesce(Sum('amount', filter=Q(ordered_date__date__gt=month)),0.0),
                    amount_last=Coalesce(Sum('amount', filter=(Q(ordered_date__date__lt=month)&Q(ordered_date__date__gte=(month - timedelta(days=30))))),0.0),
                ) 
                if time=='month':
                    month=pd.to_datetime(time_choice)
                    total_order=Order.objects.filter(shop=shop,ordered_date__month=month.month,ordered_date__year=month.year,ordered=ordered,accepted__in=accepted,canceled=canceled,received__in=received).annotate(day=TruncDay('ordered_date')).values('day').annotate(count=Count('id')).values('day','count')
                    total_amount=Order.objects.filter(shop=shop,ordered_date__month=month.month,ordered_date__year=month.year,ordered=ordered,accepted__in=accepted,canceled=canceled,received__in=received).annotate(day=TruncDay('ordered_date')).values('day').annotate(sum=Sum('amount')).values('day','sum')
                    result =Order.objects.filter(shop=shop,ordered=ordered,accepted__in=accepted,canceled=canceled,received__in=received,ordered_date__year=month.year).aggregate(
                    order=Count('id', filter=Q(ordered_date__month=month.month)),
                    order_last=Count('id', filter=Q(ordered_date__month=(month.month - 1))),
                    amount=Coalesce(Sum('amount', filter=Q(ordered_date__month=month.month)),0.0),
                    amount_last=Coalesce(Sum('amount', filter=Q(ordered_date__month=(month.month - 1))),0.0),
                    )
                    day_last_month = pd.Period(month,freq='M').end_time.date() 
                    day_months=[int((day_last_month-datetime.timedelta(days=i)).strftime('%d')) for i in range(int(day_last_month.strftime('%d')))]
                day_months.sort()
                sum_day_month=[0 for i in range(30)]
                count_day_month=[0 for i in range(30)]
                sum_day_month=[0 for i in range(30)]
                count_day_month=[0 for i in range(30)]
                for i in total_amount:
                    total_amount_months.append(i['sum'])
                    day_month.append(i['day'].strftime("%d"))
                    for j in range(len(day_months)):
                        if int(i['day'].strftime("%d")) ==day_months[j]:
                            day_months[j]=int(i['day'].strftime("%d"))
                            sum_day_month[j]=int(i['sum'])
                
                for i in total_order:
                    total_order_months.append(i['count'])
                    day_month.append(i['day'].strftime("%d"))
                    for j in range(len(day_months)):
                        if int(i['day'].strftime("%d")) ==day_months[j]:
                            day_months[j]=i['day'].strftime("%d")
                            count_day_month[j]=int(i['count'])
                
                data={
                    'result':result,
                    'total_amount':total_amount_months,'total_order':total_order_months,
                    'time':day_months,'sum':sum_day_month,'count':count_day_month,'month':month.month
                    }       
                return Response(data)

            #-----------------------------------month---------------------------------
            #------------------------------------year---------------------------------

            elif time=='year':
                year=pd.to_datetime(time_choice)
                total_order=Order.objects.filter(shop=shop,ordered_date__year=year.year,ordered=ordered).annotate(day=TruncMonth('ordered_date')).values('day').annotate(count=Count('id')).values('day','count')
                total_amount=Order.objects.filter(shop=shop,ordered_date__year=year.year,ordered=ordered).annotate(day=TruncMonth('ordered_date')).values('day').annotate(sum=Sum('amount')).values('day','sum')
                result =Order.objects.filter(shop=shop,ordered_date__year=year.year,ordered=ordered,accepted__in=accepted,canceled=canceled,received__in=received).aggregate(
                    order=Count('id', filter=Q(ordered_date__year=year.year)),
                    order_last=Count('id', filter=Q(ordered_date__year=(year.year - 1))),
                    amount=Coalesce(Sum('amount', filter=Q(ordered_date__year=year.year)),0.0),
                    amount_last=Coalesce(Sum('amount', filter=Q(ordered_date__year=(year.year - 1))),0.0),
                )
                total_amount_months=[]
                total_order_months=[]
                month_number=[]
                month_year= [i for i in range(1,13)]
                sum_month=[0 for i in range(1,13)]
                count_month=[0 for i in range(1,13)]
                if year.year==current_date.year:
                    month_year= [i for i in range(1,13)]
                    sum_month=[0 for i in range(int(current_date.month))]
                    count_month=[0 for i in range(int(current_date.month))]
                else:
                    month_year= [i for i in range(1,13)]
                    sum_month=[0 for i in range(1,13)]
                    count_month=[0 for i in range(1,13)]
                for i in total_amount:
                    total_amount_months.append(i['sum'])
                    month_number.append(i['day'].strftime("%m"))
                    for j in range(len(month_year)):
                        if int(i['day'].strftime("%m")) ==j:
                            month_year[j-1]=int(i['day'].strftime("%m"))
                            sum_month[j-1]=float(i['sum'])
                
                for i in total_order:
                    total_order_months.append(i['count'])
                    month_number.append(i['day'].strftime("%m"))
                    for j in range(len(month_year)):
                        if int(i['day'].strftime("%m")) ==j:
                            month_year[j-1]=int(i['day'].strftime("%m"))
                            count_month[j-1]=int(i['count'])
                
                data={    
                    'result':result,
                    'time':month_year,'sum':sum_month,'count':count_month,'month_number':month_number
                    }
                return Response(data)

            #-----------------------------------------year------------------------------

            #--------------------------------------current_date---------------------------
        else:
            total_amount_days=[]
            total_order_days=[]
            hour_number=[]
            hour = [i for i in range(24)]
            sum_hour=[0 for i in range(current_date.hour+1)]
            count_hour=[0 for i in range(current_date.hour+1)]
            for i in total_amount:
                total_amount_days.append(round(i['sum'],1))
                hour_number.append(i['day'].strftime("%I %p"))
                for j in hour:
                    if i['day'].strftime("%I %p") ==datetime.time(j).strftime('%I %p'):
                        hour[j]=int(i['day'].strftime("%H"))
                        sum_hour[j]=round((i['sum']),1)
        
            for i in total_order:
                total_order_days.append(i['count'])
                hour_number.append(i['day'].strftime("%I %p"))
                for j in hour:
                    if i['day'].strftime("%I %p") ==datetime.time(j).strftime('%I %p'):
                        hour[j]=int(i['day'].strftime("%H"))
                        count_hour[j]=int(i['count'])
            hours=[datetime.time(i).strftime('%H:00') for i in hour] 

            data={
                'result':result,
                'total_amount':total_amount_days,'total_order':total_order_days,
                'time':hours,'sum':sum_hour,'count':count_hour,'current_date':current_date.strftime("%Y-%m-%d")
                }
            return Response(data)




   


