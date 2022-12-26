from django.shortcuts import render
# Create your views here.
import itertools
import re
from django.db.models import F
from django.core.serializers import serialize
from account.models import *
from shop.models import *
from shipping.models import *
from orderactions.models import *
from categories.models import *
from orders.models import *
from discounts.models import *
from chats.models import *
from carts.models import *
from django.db.models import FloatField,IntegerField
from django.db.models import Max, Min, Count, Avg,Sum,F,Value as V
from django.core import serializers
from django.db.models import  Q
from calendar import weekday, day_name
import random
from django.db.models import Case, When
from django.utils import timezone
from datetime import timedelta
import datetime
from django.db.models.functions import Coalesce
from django.db.models.functions import ExtractYear, ExtractMonth,ExtractHour,ExtractHour,ExtractDay,TruncDay,TruncHour,TruncMonth
from rest_framework.views import APIView
from rest_framework.generics import (
    ListAPIView, RetrieveAPIView, CreateAPIView,
    UpdateAPIView, DestroyAPIView
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
import pytz
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
timezones = pytz.timezone('Asia/Ho_Chi_Minh')
def safe_div(x,y):
    if y == 0:
        return x
    return x / y

def datapromotion(shop,week,choice,orders,orders_last):
    data={}
    orders=orders.filter(ordered_date__date__gte=week)
    orders_last=orders_last.filter(Q(ordered_date__date__lt=week)&Q(ordered_date__date__gte=(week - timedelta(days=7))))
    
    if choice=='voucher':
        vouchers=Voucheruser.objects.filter(voucher__shop=shop)
        orders=orders.exclude(voucher=None)
        orders_last=orders_last.exclude(voucher=None)
        vouchers_user=vouchers.filter(created__date__gte=week)
        vouchers_user_last=vouchers.filter(Q(created__date__lt=week)&Q(created__date__gte=(week - timedelta(days=7))))
        count_use_voucher=orders.count()
        count_use_voucher_last=orders_last.count()
        count_voucher_received=vouchers_user.count()
        count_voucher_received_last=vouchers_user_last.count()
        usage_rate=safe_div(count_use_voucher,count_voucher_received)
        usage_rate_last=safe_div(count_use_voucher_last,count_voucher_received_last)
        data.update({'usage_rate':usage_rate,'usage_rate_last':usage_rate_last})
    elif choice=='offer':
        orders=orders.exclude(follower_offer=None)
        orders_last=orders_last.exclude(follower_offer=None)
        shopviews=ShopViews.objects.filter(shop=shop)
        number_views=shopviews.filter(create_at__date__gte=week).count()
        followers=Follower.objects.filter(shop=shop).exclude(follow_offer=None)
        number_views_last=shopviews.filter(Q(create_at__date__lt=week)&Q(create_at__date__gte=(week - timedelta(days=7)))).count()
        number_followers=followers.filter(created__date__gte=week).count()
        number_followers_last=followers.filter(Q(created__date__lt=week)&Q(created__date__gte=(week - timedelta(days=7)))).count()
        data.update({
            'number_followers':number_followers,'number_followers_last':number_followers_last
            ,'number_views':number_views,'number_views_last':number_views_last})
    
    elif choice=='award':
        orders=orders.exclude(award=None)
        orders_last=orders_last.exclude(award=None)
        gamers=Gammer.objects.filter(shop_award__shop=shop)
        number_plays=gamers.filter(shop_award__shop=shop)
        number_gamers=number_plays.order_by('user').distinct('user').count()
        number_plays_last=gamers.filter(Q(created__date__lt=week)&Q(created__date__gte=(week - timedelta(days=7))))    
        number_gamers_last=number_plays_last.order_by('user').distinct('user').count()
        data.update({
            'number_plays':number_plays,'number_plays_last':number_plays_last
            ,'number_gamers':number_gamers,'number_gamers_last':number_gamers_last})
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

class DataFollowerAPI(APIView):
    def get(self,request):
        current_date=datetime.datetime.now(tz=timezones)
        week=current_date-timedelta(days=7)
        shop=Shop.objects.get(user=request.user)
        orders=Order.objects.filter(shop=shop,accepted=True)
        orders_last=orders
        choice='offer'
        datapromotion(shop,week,choice,orders,orders_last)
        return Response(datapromotion(shop,week,choice,orders,orders_last))

class DataShopAwardAPI(APIView):
    def get(self,request):
        current_date=datetime.datetime.now(tz=timezones)
        week=current_date-timedelta(days=7)
        shop=Shop.objects.get(user=request.user)
        orders=Order.objects.filter(shop=shop,accepted=True)
        orders_last=orders
        choice='award'
        datapromotion(shop,week,choice,orders,orders_last)
        return Response(datapromotion(shop,week,choice,orders,orders_last))

class DataVoucherAPI(APIView):
    def get(self,request):
        current_date=datetime.datetime.now(tz=timezones)
        week=current_date-timedelta(days=7)
        shop=Shop.objects.get(user=request.user)
        orders=Order.objects.filter(shop=shop,accepted=True)
        choice='voucher'
        orders_last=orders
        datapromotion(shop,week,choice,orders,orders_last)
        return Response(datapromotion(shop,week,choice,orders,orders_last))

class DataAddonAPI(APIView):
    def get(self,request):
        current_date=datetime.datetime.now(tz=timezones)
        week=current_date-timedelta(days=7)
        shop=Shop.objects.get(user=request.user)
        orders=Order.objects.filter(shop=shop,accepted=True)
        orders_last=orders
        choice='addon'
        datapromotion(shop,week,choice,orders,orders_last)
        return Response(datapromotion(shop,week,choice,orders,orders_last))

class DataBundleAPI(APIView):
    def get(self,request):
        current_date=datetime.datetime.now(tz=timezones)
        week=current_date-timedelta(days=7)
        shop=Shop.objects.get(user=request.user)
        orders=Order.objects.filter(shop=shop,accepted=True)
        orders_last=orders
        choice='bundle'
        datapromotion(shop,week,choice,orders,orders_last)
        return Response(datapromotion(shop,week,choice,orders,orders_last))

class DataFlashsaleAPI(APIView):
    def get(self,request):
        current_date=datetime.datetime.now(tz=timezones)
        week=current_date-timedelta(days=7)
        shop=Shop.objects.get(user=request.user)
        orders=Order.objects.filter(shop=shop,accepted=True)
        orders_last=orders
        choice='flashsale'
        datapromotion(shop,week,choice,orders,orders_last)
        return Response(datapromotion(shop,week,choice,orders,orders_last))

class DataDiscountAPI(APIView):
    def get(self,request):
        current_date=datetime.datetime.now(tz=timezones)
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
        
        time_last=yesterday
        times = [i for i in range(25)]
        if time=='currentday':
            times=[i for i in range(current_date.hour+1)]
            orders=orders.filter(ordered_date__date__gte=current_date).annotate(day=TruncHour('ordered_date'))
            orders_last=orders_last.filter(ordered_date__date=(current_date - timedelta(days=1)))
        if time=='day':
            days=pd.to_datetime(time_choice)
            
            orders=orders.filter(ordered_date__date=time_choice).annotate(day=TruncHour('ordered_date'))
            orders_last=orders_last.filter(Q(ordered_date__date=(days - timedelta(days=1))))
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
            times=[int((day_first_week + datetime.timedelta(days=i)).date().strftime('%d')) for i in range(7)] 
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
            orders_last=orders_last.filter(Q(ordered_date__date__lt=month)&Q(ordered_date__date__gte=(month - timedelta(days=30)))) 
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
        elif choice=='offer':
            orders=orders.exclude(follower_offer=None)
            orders_last=orders_last.exclude(follower_offer=None)
            discount_voucher=orders.aggregate(sum=Coalesce(Sum('discount_offer'),0.0))
            discount_voucher_last=orders_last.aggregate(sum=Coalesce(Sum('discount_offer'),0.0))
            data.update({
            'discount_voucher_last':discount_voucher_last['sum'],
            'discount_voucher':discount_voucher['sum']})
        elif choice=='award':
            orders=orders.exclude(award=None)
            orders_last=orders_last.exclude(award=None)
            
        else:
            cartitems=CartItem.objects.filter(order_cartitem__in=orders)
            cartitems_last=cartitems
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
            total_quantity=cartitems.aggregate(sum=Coalesce(Sum('quantity'),0))
            total_quantity_last=cartitems_last.aggregate(sum=Coalesce(Sum('quantity'),0))
            data.update({'total_quantity':total_quantity['sum'],
            'total_quantity_last':total_quantity_last['sum']})
        list_total_order=orders.values('day').annotate(count=Count('id')).values('day','count')
        list_total_amount=orders.values('day').annotate(sum=Coalesce(Sum('amount'),0.0)).values('day','sum')
        number_buyer=orders.order_by('user').distinct('user').count()
        total_amount=orders.aggregate(sum=Coalesce(Sum('amount'),0.0))
        total_order=orders.aggregate(count=Count('id'))
        number_buyer_last=orders_last.order_by('user').distinct('user').count()
        total_amount_last=orders_last.aggregate(sum=Coalesce(Sum('amount'),0.0))
        total_order_last=orders_last.aggregate(count=Count('id'))
        times.sort()
        return {'number_buyer':number_buyer,**data,'times':times,
        'total_amount':total_amount['sum'],'total_order_last':total_order_last['count'],
        'number_buyer_last':number_buyer_last,
        'total_amount_last':total_amount_last['sum'],'total_order':total_order['count'],
        'count':list(list_total_order),'sum':list(list_total_amount)}
        
class DashboardDiscountAPI(APIView):
    def get(self,request):
        current_date=datetime.datetime.now(tz=timezones)
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
        current_date=datetime.datetime.now(tz=timezones)
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
        current_date=datetime.datetime.now(tz=timezones)
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
        vouchers_user_last=vouchers
        if time=='currentday':
            vouchers_user=vouchers_user.filter(created__date__gte=current_date)
            vouchers_user_last=vouchers_user_last.filter(created__date=(current_date - timedelta(days=1))) 
        if time=='day':
            day=pd.to_datetime(time_choice)
            vouchers_user_last=vouchers_user_last.filter(Q(created__date=(day - timedelta(days=1))))
        if time=='yesterday':
            vouchers_user=vouchers_user.filter(created__date=yesterday)
            vouchers_user_last=vouchers_user_last.filter(Q(created__date=(yesterday - timedelta(days=1))))
        if time=='week_before':
            vouchers_user=vouchers_user.filter(created__date__gte=week,created__date__lte=yesterday)
            vouchers_user_last=vouchers_user_last.filter(Q(created__date__lt=week)&Q(created__date__gte=(week - timedelta(days=7))))
        if time=='week':  
            week=pd.to_datetime(time_choice)
            vouchers_user_last=vouchers_user_last.filter(Q(created__week=(week.isocalendar()[1] - 1)))
        if time=='month': 
            month=pd.to_datetime(time_choice)
            vouchers_user=vouchers_user.filter(created__month=month.month,created__year=month.year)
            vouchers_user_last=vouchers_user_last.filter(Q(created__month=(month.month - 1)) & Q(created__year=month.year))
        if time=='month_before':
            vouchers_user=vouchers_user.filter(created__date__gte=month,created__date__lte=yesterday)
            vouchers_user_last=vouchers_user_last.filter(Q(created__date__lt=month)&Q(created__date__gte=(month - timedelta(days=30)))) 
        if time=='year':
            year=pd.to_datetime(time_choice)
            vouchers_user=vouchers_user.filter(ordered_date__year=year.year)
            vouchers_user_last=vouchers_user_last.filter(Q(ordered_date__year=(year.year - 1))) 
        data={'count_voucher_received':vouchers_user.count(),'count_voucher_received_last':vouchers_user_last.count()}
        datachart={**data,**dashboard(shop,time,time_choice,choice,orders,orders_last,current_date,yesterday,week,month)}
        return Response(datachart)

class DashboardFlashsaleAPI(APIView):
    def get(self,request):
        shop=Shop.objects.get(user=request.user)
        current_date=datetime.datetime.now(tz=timezones)
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
        current_date=datetime.datetime.now(tz=timezones)
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

class DashboardAwardAPI(APIView):
    def get(self,request):
        shop=Shop.objects.get(user=request.user)
        current_date=datetime.datetime.now(tz=timezones)
        yesterday=current_date-timedelta(days=1)
        week=current_date-timedelta(days=7)
        month=current_date-timedelta(days=30)
        time=request.GET.get('time')
        choice='award'
        time_choice=request.GET.get('time_choice')
        orders=Order.objects.filter(shop=shop,accepted=True)
        orders_last=orders
        gamers=Gammer.objects.filter(shop_award__shop=shop)
        gamers_last=Gammer.objects.filter(shop_award__shop=shop)
        number_plays=gamers.filter(shop_award__shop=shop)
        data={}
        if time=='currentday':
            gamers=gamers.filter(created__date__gte=current_date)
            gamers_last=gamers_last.filter(created__date=(current_date - timedelta(days=1)))
            
        if time=='day':
            days=pd.to_datetime(time_choice)
            gamers=gamers.filter(created__date=time_choice)
            gamers_last=gamers_last.filter(Q(created__date=(days - timedelta(days=1))))
        if time=='yesterday':
            gamers=gamers.filter(created__date=yesterday)
            gamers_last=gamers_last.filter(Q(created__date=(yesterday - timedelta(days=1))))
        if time=='week_before': 
            gamers=gamers.filter(created__date__gte=week,created__date__lte=yesterday)
            gamers_last=gamers_last.filter(Q(created__date__lt=week)&Q(created__date__gte=(week - timedelta(days=7))))
        if time=='week': 
            week=pd.to_datetime(time_choice)
            day_first_week=week - datetime.timedelta(days=week.isoweekday() % 7)
            gamers=gamers.filter(created__week=week.isocalendar()[1],created__year=week.year)
            gamers_last=gamers_last.filter(Q(created__week=(week.isocalendar()[1] - 1)))
        if time=='month': 
            month=pd.to_datetime(time_choice)
            day_last_month = pd.Period(month,freq='M').end_time.date() 
            gamers=gamers.filter(created__month=month.month,created__year=month.year)
            gamers_last=gamers_last.filter(Q(created__month=(month.month - 1)))
        if time=='month_before':  
            gamers=gamers.filter(created__date__gte=month,created__date__lte=yesterday)
            gamers_last=gamers_last.filter(Q(created__date__lt=month)&Q(created__date__gte=(month - timedelta(days=30)))) 
        if time=='year':
            year=pd.to_datetime(time_choice)
            gamers=gamers.filter(created__year=year.year)
            gamers_last=gamers_last.filter(Q(created__year=(year.year - 1)))
        number_plays=gamers.count()
        number_plays_last=gamers_last.count()
        number_gamers=gamers.order_by('user').distinct('user').count()
        number_gamers_last=gamers_last.order_by('user').distinct('user').count()
        award_received=gamers.exclude(award=None)
        award_received_last=gamers.exclude(award=None)
        bulgets=award_received.aggregate(sum=Coalesce(Sum((F('award__quantity')*F('award__maximum_discount')),output_field=FloatField()),0.0))
        bulgets_last=award_received_last.aggregate(sum=Coalesce(Sum((F('award__quantity')*F('award__maximum_discount')),output_field=FloatField()),0.0))
        data.update({
        'number_plays':number_plays,'number_plays_last':number_plays_last,
        'bulgets':bulgets['sum'],'bulgets_last':bulgets_last['sum'],
        'award_received':award_received.count(),'award_received_last':award_received_last.count()
        ,'number_gamers':number_gamers,'number_gamers_last':number_gamers_last})
        dashboard(shop,time,time_choice,choice,orders,orders_last,current_date,yesterday,week,month)
        datadashboard={**data,**dashboard(shop,time,time_choice,choice,orders,orders_last,current_date,yesterday,week,month)}
        return Response(datadashboard)

class DashboardOfferAPI(APIView):
    def get(self,request):
        shop=Shop.objects.get(user=request.user)
        current_date=datetime.datetime.now(tz=timezones)
        yesterday=current_date-timedelta(days=1)
        week=current_date-timedelta(days=7)
        month=current_date-timedelta(days=30)
        time=request.GET.get('time')
        choice='offer'
        time_choice=request.GET.get('time_choice')
        orders=Order.objects.filter(shop=shop,accepted=True)
        orders_last=orders
        shopviews=ShopViews.objects.filter(shop=shop)
        shopviews_last=shopviews
        followers=Follower.objects.filter(shop=shop).exclude(follow_offer=None)
        followers_last=followers
        if time=='currentday':
            shopviews=shopviews.filter(create_at__date__gte=current_date)
            shopviews_last=shopviews_last.filter(create_at__date=(current_date - timedelta(days=1))) 
            followers=followers.filter(created__date__gte=current_date)
            followers_last=followers_last.filter(created__date=(current_date - timedelta(days=1))) 
        if time=='day':
            days=pd.to_datetime(time_choice)
            shopviews=shopviews.filter(create_at__date=time_choice)
            shopviews_last=shopviews_last.filter(Q(create_at__date=(days - timedelta(days=1)))) 
            followers=followers.filter(created__date=time_choice)
            followers_last=followers_last.filter(Q(created__date=(days - timedelta(days=1)))) 
        if time=='yesterday':
            shopviews=shopviews.filter(create_at__date=yesterday)
            shopviews_last=shopviews_last.filter(Q(create_at__date=(yesterday - timedelta(days=1)))) 
            followers=followers.filter(created__date=yesterday)
            followers_last=followers_last.filter(Q(created__date=(yesterday - timedelta(days=1)))) 
        if time=='week_before':
            shopviews=shopviews.filter(create_at__date__gte=week)
            shopviews_last=shopviews_last.filter(Q(create_at__date__lt=week)&Q(create_at__date__gte=(week - timedelta(days=7))))
            followers=followers.filter(created__date__gte=week)
            followers_last=followers_last.filter(Q(created__date__lt=week)&Q(created__date__gte=(week - timedelta(days=7))))
        if time=='week':  
            week=pd.to_datetime(time_choice)
            shopviews=shopviews.filter(create_at__week=week.isocalendar()[1],create_at__year=week.year)
            shopviews=shopviews.filter(create_at__week=week.isocalendar()[1],create_at__year=week.year)
            followers=followers.filter(created__week=week.isocalendar()[1],created__year=week.year)
            followers_last=followers_last.filter(Q(created__week=(week.isocalendar()[1] - 1)) & Q(created__year=week.year))
        if time=='month': 
            month=pd.to_datetime(time_choice)
            shopviews=shopviews.filter(create_at__month=month.month,create__year=month.year)
            shopviews_last=shopviews_last.filter(Q(create_at__month=(month.month - 1)) & Q(create_at__year=month.year))
            followers=followers.filter(created__month=month.month,created__year=month.year)
            followers_last=followers_last.filter(Q(created__month=(month.month - 1)) & Q(created__year=month.year))
        if time=='month_before':
            shopviews=shopviews.filter(create_at__date__gte=month,created__date__lte=yesterday)
            shopviews_last=shopviews_last.filter(Q(create_at__date__lt=month)&Q(created__date__gte=(month - timedelta(days=30)))) 
            followers=followers.filter(created__date__gte=month,created__date__lte=yesterday)
            followers_last=followers_last.filter(Q(created__date__lt=month)&Q(created__date__gte=(month - timedelta(days=30)))) 
        if time=='year':
            year=pd.to_datetime(time_choice)
            shopviews=shopviews.filter(create_at__year=year)
            shopviews_last=shopviews_last.filter(Q(create_at__year=(year.year - 1))) 
            followers=followers.filter(created__year=year)
            followers_last=followers_last.filter(Q(created__year=(year.year - 1))) 
        number_followers=followers.count()
        number_followers_last=followers_last.count()
        number_views_last=shopviews_last.count()
        number_views=shopviews.count()
        data={'number_followers':number_followers,
         'number_followers_last':number_followers_last,'number_views':number_views,
         'number_views_last':number_views_last}
        dashboard(shop,time,time_choice,choice,orders,orders_last,current_date,yesterday,week,month)
        datadashboard={**data,**dashboard(shop,time,time_choice,choice,orders,orders_last,current_date,yesterday,week,month)}
        return Response(datadashboard)

class MyDashboard(APIView):
    def get(self,request):
        user=request.user
        shop=Shop.objects.get(user=user)
        current_date=datetime.datetime.now(tz=timezones)
        yesterday=current_date-timedelta(days=1)
        week=current_date-timedelta(days=7)
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
        if typeorder=='received':
            received=[True]
        orders=Order.objects.filter(shop=shop,ordered=True,received__in=received,canceled=canceled,accepted__in=accepted)
        orders_last=orders
        data={}
        #--------------------------day-------------------------------
        times = [i for i in range(25)]
        if time=='currentday':
            times=[i for i in range(current_date.hour+1)]
            orders=orders.filter(ordered_date__date__gte=current_date).annotate(day=TruncHour('ordered_date'))
            orders_last=orders_last.filter(ordered_date__date=(current_date - timedelta(days=1)))
        if time=='day':
            days=pd.to_datetime(time_choice)
            orders=orders.filter(ordered_date__date=time_choice).annotate(day=TruncHour('ordered_date'))
            orders_last=orders_last.filter(Q(ordered_date__date=(days - timedelta(days=1))))
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
            times=[int((day_first_week + datetime.timedelta(days=i)).date().strftime('%d')) for i in range(7)] 
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
            orders_last=orders_last.filter(Q(ordered_date__date__lt=month)&Q(ordered_date__date__gte=(month - timedelta(days=30)))) 
        if time=='year':
            times=[i for i in range(1,13)]
            year=pd.to_datetime(time_choice)
            orders=orders.filter(ordered_date__year=year.year).annotate(day=TruncMonth('ordered_date'))
            orders_last=orders_last.filter(Q(ordered_date__year=(year.year - 1)))
        times.sort()
        list_total_order=orders.values('day').annotate(count=Count('id')).values('day','count')
        list_total_amount=orders.values('day').annotate(sum=Coalesce(Sum('amount'),0.0)).values('day','sum')
        total_amount=orders.aggregate(sum=Coalesce(Sum('amount'),0.0))
        total_order=orders.aggregate(count=Count('id'))
        total_amount_last=orders_last.aggregate(sum=Coalesce(Sum('amount'),0.0))
        total_order_last=orders_last.aggregate(count=Count('id'))
        datadashboard ={**data,'times':times,
        'total_amount':total_amount['sum'],'total_order_last':total_order_last['count'],
        'total_amount_last':total_amount_last['sum'],'total_order':total_order['count'],
        'count':list(list_total_order),'sum':list(list_total_amount)}
        return Response(datadashboard)