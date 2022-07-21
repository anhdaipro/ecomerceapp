from django.contrib.auth import login
import itertools
import re
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
from django.db.models import FloatField
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

class ListcomboAPI(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ComboSerializer
    def get_queryset(self):
        request = self.request
        user=request.user
        shop=Shop.objects.get(user=user)
        return Promotion_combo.objects.filter(shop=shop).prefetch_related('products__media_upload')

class ListdealshockAPI(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = BuywithsockdealSerializer
    def get_queryset(self):
        request = self.request
        user=request.user
        shop=Shop.objects.get(user=user)
        return Buy_with_shock_deal.objects.filter(shop=shop).prefetch_related('main_products__media_upload').prefetch_related('byproducts__media_upload')

class ListprogramAPI(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ShopProgramSerializer
    def get_queryset(self):
        request = self.request
        user=request.user
        shop=Shop.objects.get(user=user)
        return Shop_program.objects.filter(shop=shop).prefetch_related('products__media_upload')

class ListflashsaleAPI(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = FlashSaleSerializer
    def get_queryset(self):
        request = self.request
        user=request.user
        shop=Shop.objects.get(user=user)
        return Flash_sale.objects.filter(shop=shop).prefetch_related('products__media_upload')

class ShopprofileAPIView(APIView):
    def get(self,request):
        user=request.user
        shop=Shop.objects.get(user=user)
        description_url=shop.description_url.all()
        data={'image_cover':shop.get_image(),'name':shop.name,'description':shop.description,'description_url':[{'image':i.get_image(),'url':i.url_field} for i in description_url]}
        return Response(data)
    def post(self,request):
        list_file=request.FILES.getlist('file')
        list_url=request.POST.getlist('url')
        avatar=request.FILES.get('avatar')
        image_cover=request.FILES.get('image_cover')
        name=request.POST.get('name')
        description=request.POST.get('description')
        shop=Shop.objects.get(user=request.user)
        profile=Profile.objects.get(user=request.user)
        shop.name=name
        shop.description=description
        for url in list_url:
            Image_home.objects.create(url_field=url,upload_by=request.user)
        for file in list_file:
            Image_home.objects.create(image=file,upload_by=request.user)
        
        if image_cover:
            shop.image_cover=image_cover
        if avatar:
            profile.avatar=avatar
        shop.save()
        count=len(list_url)+len(list_file)
        list_image=Image_home.objects.filter(upload_by=request.user).order_by('-id')[:count]
        shop.description_url.add(*list_image)
        profile.save()
        data={'ok':'ok'}
        return Response(data)

@api_view(['GET', 'POST'])
def infoseller(request):
    user=request.user
    profile=Profile.objects.get(user=user)
    address=Address.objects.filter(user=user,address_type='B')
    data={'name':user.username,'image':profile.avatar.url,'user_type':profile.user_type,'phone':str(profile.phone)}
    return Response(data)

@api_view(['GET', 'POST'])
def homeseller(request):
    user=request.user
    shop=Shop.objects.get(user=user)
    current_date=datetime.datetime.now()
    count_order_waiting_comfirmed=Order.objects.filter(shop=shop,ordered=True,canceled=False,accepted=False,being_delivered=False,received=False,accepted_date__gt=timezone.now()).count()
    count_order_canceled=Order.objects.filter(shop=shop,ordered=True,canceled=True).count()
    count_order_processed=Order.objects.filter(shop=shop,ordered=True,canceled=False,accepted=True,received=False,being_delivered=False).count()
    count_order_waiting_processed=Order.objects.filter(shop=shop,ordered=True,being_delivered=False,accepted=False,accepted_date__lt=timezone.now()).count()
    total_order_day=Order.objects.filter(shop=shop,ordered=True,ordered_date__date__gte=current_date).annotate(day=TruncHour('ordered_date')).values('day').annotate(count=Count('id')).values('day','count')
    total_amount_day=Order.objects.filter(shop=shop,ordered=True,ordered_date__date__gte=current_date).annotate(day=TruncHour('ordered_date')).values('day').annotate(sum=Sum('amount')).values('day','sum')
    total_amount_days=[]
    total_order_days=[]
    hour_number=[]   
    total_amount_days=[]
    total_order_days=[]
    hour_number=[]       
    hour = [i for i in range(24)]
    sum_hour=[0 for i in range(current_date.hour+1)]
    count_hour=[0 for i in range(current_date.hour+1)]
    for i in total_amount_day:
        total_amount_days.append(i['sum'])
        hour_number.append(i['day'].strftime("%d %I %p"))
        for j in hour:
            if i['day'].strftime("%I %p") ==datetime.time(j).strftime('%I %p'):
                hour[j]=int(i['day'].strftime("%H"))
                sum_hour[j]=round((i['sum']),1)
        
    for i in total_order_day:
        total_order_days.append(i['count'])
        hour_number.append(i['day'].strftime("%I %p"))
        for j in hour:
            if i['day'].strftime("%I %p") ==datetime.time(j).strftime('%I %p'):
                hour[j]=int(i['day'].strftime("%H"))
                count_hour[j]=int(i['count'])
    current_date.strftime('%d')
    hours=[datetime.time(i).strftime('%H:00') for i in hour] 
    data={
    'hours':hours,'sum':sum_hour,'count':count_hour,'count_order_waiting_comfirmed':count_order_waiting_comfirmed,
    'count_order_canceled':count_order_canceled,'count_order_processed':count_order_processed,
    'count_order_waiting_processed':count_order_waiting_processed
    }
    return Response(data)

class Listordershop(APIView):
    def get(self,request):
        shop=Shop.objects.get(user=request.user)
        orders=Order.objects.filter(shop=shop,ordered=True).prefetch_related('items__item__media_upload').prefetch_related('items__item__promotion_combo').prefetch_related('items__item__byproduct').prefetch_related('items__item__shop_program').prefetch_related('items__product__color').prefetch_related('items__product__size').prefetch_related('items__byproduct_cart')
        type_order=request.GET.get('type')
        source=request.GET.get('source')
        if type_order:
            if type_order=='toship':
                orders=orders.filter(accepted_date__lt=timezone.now())
                if source=='processed':
                    orders=orders.filter(accepted=True,being_delivered=False,received=False,canceled=False)
            if type_order=='shipping':
                orders=orders.filter(being_delivered=True,received=False,canceled=False) 
            if type_order=='completed':
                orders=orders.filter(received=True) 
            if type_order=='canceled':
                orders=orders.filter(canceled=True) 
            if type_order=='refund':
                orders=orders.exclude(refund=None)
        data=OrdersellerSerializer(orders,many=True).data
        return Response(data)

    def post(self,request):
        id=request.POST.get('id')
        order=Order.objects.get(id=id)
        order.accepted=True
        order.save()
        return Response(data)

class ShopratingAPI(APIView):
    def get(self,request):
        shop=Shop.objects.get(user=request.user)
        list_review=ReView.objects.filter(cartitem__shop=shop).distinct()
        page=request.GET.get('page')
        paginator = Paginator(list_review,5)
        page_obj = paginator.get_page(page)
        count_review=list_review.count()
        data={'reviews':ReviewshopSerializer(page_obj,many=True).data,'page_count':paginator.num_pages}
        return Response(data) 
    def post(self,request):
        text=request.POST.get('text')
        id=request.POST.get('id')
        review=ReView.objects.get(id=id)
        reply=Reply.objects.create(text=text,review=review,user=request.user)
        data={'id':reply.id,'text':reply.text}
        return Response(data)

@api_view(['GET', 'POST'])
def product(request):
    user=request.user
    shop=Shop.objects.get(user=user)
    items=Item.objects.filter(shop=shop)
    item_id=request.GET.get('item_id')
    page_no=request.GET.get('page_no')
    per_page=request.GET.get('per_page')
    order=request.GET.get('order')
    price=request.GET.get('price')
    inventory=request.GET.get('inventory')
    sort=request.GET.get('sort')
    if request.method=="POST":
        item_id=request.POST.getlist('item_id')
        Item.objects.filter(id__in=item_id).delete()
        data={
            'count_product':items.count()
        }
        return Response(data)
    else:
        if item_id:
            items=Item.objects.get(id=item_id)     
        if price and sort:
            if sort == "sort-asc":
                items=items.order_by('variation__price').distinct()
            else:
                items=items.order_by('-variation__price').distinct()
            
            return Response(data)
        if order and sort:
            if sort == "sort-asc":
                items=items.annotate(count=Count('variation__cartitem__order__id')).order_by('count')
            else:
                items=items.annotate(count=Count('variation__cartitem__order__id')).order_by('-count')
            
            return Response(data)
        if inventory and sort:
            if sort == "sort-asc":
                items=items.order_by('variation__inventory').distinct()
            else:
                items=items.order_by('-variation__inventory').distinct()
        obj_paginator = Paginator(items, per_page)
        first_page = obj_paginator.get_page(1)
        if page_no:
            first_page = obj_paginator.get_page(page_no)   
        variations=Variation.objects.filter(item__in=first_page).order_by('-color__value')
        list_product=ItemproductSerializer(first_page,many=True).data
        list_variation=VariationsellerSerializer(variations,many=True).data
        data={
            'a':list_product,'b':list_variation,'page_range':obj_paginator.num_pages,'count_product':product.count()
        }
        return Response(data)

@api_view(['GET', 'POST'])
def get_product(request):
    user=request.user
    shop=Shop.objects.get(user=user)
    page=1
    pagesize=12
    list_product=Item.objects.filter(shop=shop).prefetch_related('media_upload').prefetch_related('variation_item').prefetch_related('cart_item__order_cartitem')
    page_no=request.GET.get('page')
    per_page=request.GET.get('pagesize')
    item_id=request.GET.get('item_id')
    if request.method=="POST":
        item_id=request.POST.getlist('item_id')
        Item.objects.filter(id__in=item_id).delete()
        data={
            'count_product':list_product.count()
        }
        return Response(data)
    else:
        if item_id:
            item=Item.objects.get(id=item_id)
            variations=item.variation_item.all()[2:item.variation_item.all().count()]
            data=VariationsellerSerializer(variations,many=True).data
            return Response(data)
        else:
            if page_no and per_page:
                page=int(page_no)
                pagesize=int(per_page)
            obj_paginator = Paginator(list_product, pagesize)
            pageitem = obj_paginator.get_page(page)
            data={'count_product':list_product.count(),
                    'pageitem':[{'name':item.name,'image':item.get_image_cover(),
                    'id':item.id,'sku_product':item.sku_product,
                    'count_variation':item.variation_item.all().count(),
                    'variations':VariationsellerSerializer(item.variation_item.all()[0:3],many=True).data
                    } for item in pageitem]
                }
            return Response(data)
       
@api_view(['GET', 'POST'])
def delete_product(request):
    user=request.user
    shop=Shop.objects.get(user=user)
    if request.method=="POST":
        item_id=request.POST.getlist('item_id')
        Item.objects.filter(id__in=item_id).delete()
        product=Item.objects.filter(shop=shop)
        page_no=request.POST.get('page_no')
        per_page=request.POST.get('per_page')
        obj_paginator = Paginator(product, per_page)
        first_page = obj_paginator.get_page(page_no)
        variations=Variation.objects.filter(item__in=first_page).order_by('-color__value')
        list_product=ItemproductSerializer(first_page,many=True).data
        list_variation=VariationsellerSerializer(variations,many=True).data
        data={
            'a':list_product,'b':list_variation,'page_range':obj_paginator.num_pages,'count_product':product.count()
        }
        return Response(data)

def filteritem(price,sort,order,name,q,sku,item,items):
    if price and sort:
        if sort == "sort-asc":
            items=items.order_by('variation__price').distinct()
        else:
            items=items.order_by('-variation__price').distinct()
    elif order and sort:
        if sort == "sort-asc":
            items=items.annotate(count=Count('variation__cartitem__order__id')).order_by('count')
        else:
            items=items.annotate(count=Count('variation__cartitem__order__id')).order_by('-count')
        data=ItemSellerSerializer(items,many=True).data
    elif name and q:
        category=Category.objects.get(title=title,choice=True)
        items=items.filter(name__contains=q,category=category)
        data=ItemSellerSerializer(items,many=True).data
    elif sku and q:
        category=Category.objects.get(title=title,choice=True)
        items=items.filter(sku_product=q,category=category)
    
class Newvoucher(APIView):
    def get(self,request):
        user=request.user
        shop=Shop.objects.get(user=user)
        items=Item.objects.filter(shop=shop).order_by('-id')
        order=request.GET.get('order')
        price=request.GET.get('price')
        sort=request.GET.get('sort')
        name=request.GET.get('name')
        sku=request.GET.get('sku')
        item=request.GET.get('item')
        title=request.GET.get('title')
        q=request.GET.get('q')
        filteritem(price,sort,order,name,q,sku,item,items)
        data=ItemSellerSerializer(items,many=True).data
        return Response(data)
    def post(self,request):
        shop=Shop.objects.get(user=request.user)
        items=Item.objects.filter(shop=shop).order_by('-id')
        list_items=request.data.get('list_items')
        code_type=request.data.get('code_type')
        name_of_the_discount_program=request.data.get('name_of_the_discount_program')
        code = request.data.get('code')
        valid_from=request.data.get('valid_from')
        valid_to=request.data.get('valid_to')
        discount_type=request.data.get('discount_type')
        amount = request.data.get('amount')
        percent = request.data.get('percent')
        maximum_usage=request.data.get('maximum_usage')
        voucher_type=request.data.get('voucher_type')
        maximum_discount=request.data.get('maximum_discount')
        minimum_order_value=request.data.get('minimum_order_value')
        setting_display=request.data.get('setting_display')
        vocher,created=Voucher.objects.get_or_create(
            code_type=code_type,#Loại mã
            shop=shop,
            name_of_the_discount_program=name_of_the_discount_program,
            code = code,
            valid_from=valid_from,
            valid_to=valid_to,
            discount_type= discount_type,#loại giảm giá
            amount = amount,
            percent = percent,
            maximum_usage=maximum_usage,
            maximum_discount=maximum_discount,
            voucher_type=voucher_type,
            minimum_order_value=minimum_order_value,
            setting_display=setting_display,
        )
        if vocher.code_type=="All":
            vocher.products.add(*items)
        else:
            vocher.products.add(*list_items)
        data={'ok':'ok' }
        return Response(data)

class DetailVoucher(APIView):
    def get(self,request,id):
        voucher=Voucher.objects.get(id=id)
        data=Voucherseller(voucher).data
        return Response(data)
    def post(self,request,id):
        user=request.user
        shop=Shop.objects.get(user=user)
        items=Item.objects.filter(shop=shop)
        list_items=request.data.get('list_items')
        vocher.code_type=request.data.get('code_type')
        vocher.products.set([])
        vocher.name_of_the_discount_program=request.data.get('name_of_the_discount_program')
        vocher.code = request.data.get('code')
        vocher.valid_from=request.data.get('valid_from')
        vocher.valid_to=request.data.get('valid_to')
        vocher.discount_type=request.data.get('discount_type')
        vocher.amount = request.data.get('amount')
        vocher.percent = request.data.get('percent')
        vocher.maximum_usage=request.data.get('maximum_usage')
        vocher.voucher_type=request.data.get('voucher_type')
        vocher.maximum_discount=request.data.get('maximum_discount')
        vocher.minimum_order_value=request.data.get('minimum_order_value')
        vocher.setting_display=request.data.get('setting_display')
        vocher.save()
        if vocher.code_type=="All":
            vocher.products.add(*items)
        else:
            vocher.products.add(*list_items)
        data={'ok':'ok' }
        return Response(data)
          
@api_view(['GET', 'POST'])
def shop_award(request):
    shop=Shop.objects.get(user=user)
    if request.method=="POST":
        shop_award,created=Shop_award.objects.get_or_create(
            shop=shop,
            game_name=request.POST.get("game_name"),
            valid_from=request.POST.get("valid_from"),
            valid_to=request.POST.get("valid_to"),
            discount_type= request.POST.get("discount_type"),#loại giảm giá
            amount = request.POST.get("amount"),
            percent = request.POST.get("percent"),
            minimum_order_value=request.POST.get("minimum_order_value"),
            type_voucher="Offer",
            code_number=request.POST.get("code_number")
        )
        data={'a':list_item_main,'page_range':obj_paginator.num_pages,'page_no':page_no }
        return Response(data)
    
@api_view(['GET', 'POST'])
def follower_offer(request):
    shop=Shop.objects.get(user=user)
    if request.method=="POST":
        offer_follow,created=Follower_offer.objects.get_or_create(
            shop=shop,
            name_offer=request.POST.get('offer_name'),
            valid_from=request.POST.get('valid_from'),
            valid_to=request.POST.get('valid_to'),
            discount_type=request.POST.get('discount_type'),
            amount = request.POST.get('amount'),
            percent = request.POST.get('percent'),
            maximum_usage=request.POST.get('maximum_usage'),
            type_offer="Voucher",
            voucher_type=request.POST.get('voucher_type'),
            maximum_discount=request.POST.get('maximum_discount'),
            minimum_order_value=request.POST.get('minimum_order_value'),
            max_price=request.POST.get('max-discount-price'),
        )

        data={'a':'a' }
        return Response(data)

class NewcomboAPI(APIView):
    def get(self,request):
        shop=Shop.objects.get(user=request.user)
        valid_to=request.GET.get('valid_to')
        combo_id=request.GET.get('combo_id')
        valid_from=request.GET.get('valid_from')
        shockdeals=Buy_with_shock_deal.objects.filter(((Q(valid_from__lt=valid_from)&Q(valid_to__gt=valid_to)) | (Q(valid_from__gte=valid_from)&Q(valid_to__lte=valid_to)) | (Q(valid_from__lte=valid_from) & Q(valid_to__gt=valid_from)) | (Q(valid_from__gte=valid_from) & Q(valid_to__gte=valid_from)))  & Q(valid_to__gt=datetime.datetime.now()))
        promotions=Promotion_combo.objects.filter(((Q(valid_from__lt=valid_from)&Q(valid_to__gt=valid_to)) | (Q(valid_from__gte=valid_from)&Q(valid_to__lte=valid_to)) | (Q(valid_from__lte=valid_from) & Q(valid_to__gt=valid_from)) | (Q(valid_from__gte=valid_from) & Q(valid_to__gte=valid_from)))  & Q(valid_to__gt=datetime.datetime.now()))
        if combo_id:
            promotions= promotions.exclude(id=combo_id)
        items=Item.objects.filter(shop=shop).exclude(Q(main_product__in=shockdeals) |Q(promotion_combo__in=promotions)).order_by('-id')
        order=request.GET.get('order')
        price=request.GET.get('price')
        sort=request.GET.get('sort')
        name=request.GET.get('name')
        sku=request.GET.get('sku')
        item=request.GET.get('item')
        title=request.GET.get('title')
        q=request.GET.get('q')
        filteritem(price,sort,order,name,q,sku,item,items)
        data=ItemSellerSerializer(items,many=True).data
        return Response(data)
    def post(self,request):
        shop=Shop.objects.get(user=request.user)
        valid_from=request.data.get('valid_from')
        valid_to=request.data.get('valid_to')
        list_items=request.data.get('list_items')
        shockdeals=Buy_with_shock_deal.objects.filter(((Q(valid_from__lt=valid_from)&Q(valid_to__gt=valid_to)) | (Q(valid_from__gte=valid_from)&Q(valid_to__lte=valid_to)) | (Q(valid_from__lte=valid_from) & Q(valid_to__gt=valid_from)) | (Q(valid_from__gte=valid_from) & Q(valid_to__gte=valid_from)))  & Q(valid_to__gt=datetime.datetime.now()))
        promotions=Promotion_combo.objects.filter(((Q(valid_from__lt=valid_from)&Q(valid_to__gt=valid_to)) | (Q(valid_from__gte=valid_from)&Q(valid_to__lte=valid_to)) | (Q(valid_from__lte=valid_from) & Q(valid_to__gt=valid_from)) | (Q(valid_from__gte=valid_from) & Q(valid_to__gte=valid_from)))  & Q(valid_to__gt=datetime.datetime.now()))
        items=Items.filter(shop=shop).filter(Q(main_product__in=shockdeals) |Q(promotion_combo__in=promotions))
        listitemdeal=[item.id for item in items]
        data={}
        sameitem=list(set(listitemdeal).intersection(list_items))
        if len(sameitem)==0:
            promotion_combo,created=Promotion_combo.objects.get_or_create(
                shop=shop,
                promotion_combo_name=request.data.get('promotion_combo_name'),
                valid_from=valid_from,
                valid_to=valid_to,
                combo_type=request.data.get('combo_type'),
                discount_percent=request.data.get('discount_percent'),
                discount_price=request.data.get('discount_price'),
                price_special_sale=request.data.get('price_special_sale'),
                limit_order=request.data.get('limit_order'),
                quantity_to_reduced=request.data.get('quantity_to_reduced'),
                ) 
            promotion_combo.products.add(*list_items)
            data.update({'suscess':True})
        else:
            data.update({'error':True,'sameitem':sameitem})
        return Response(data)
    
class DetailComboAPI(APIView):
    def get(self,request,id):
        promotion_combo=Promotion_combo.objects.get(id=id)
        data=CombosellerSerializer(promotion_combo).data
        return Response(data) 
    def post(self,request,id):
        list_items=request.data.get('list_items')
        valid_from=request.data.get('valid_from')
        valid_to=request.data.get('valid_to')
        promotion_combo=Promotion_combo.objects.get(id=id)
        data={}
        shockdeals=Buy_with_shock_deal.objects.filter(((Q(valid_from__lt=valid_from)&Q(valid_to__gt=valid_to)) | (Q(valid_from__gte=valid_from)&Q(valid_to__lte=valid_to)) | (Q(valid_from__lte=valid_from) & Q(valid_to__gt=valid_from)) | (Q(valid_from__gte=valid_from) & Q(valid_to__gte=valid_from)))  & Q(valid_to__gt=datetime.datetime.now()))
        promotions=Promotion_combo.objects.filter(((Q(valid_from__lt=valid_from)&Q(valid_to__gt=valid_to)) | (Q(valid_from__gte=valid_from)&Q(valid_to__lte=valid_to)) | (Q(valid_from__lte=valid_from) & Q(valid_to__gt=valid_from)) | (Q(valid_from__gte=valid_from) & Q(valid_to__gte=valid_from)))  & Q(valid_to__gt=datetime.datetime.now())).exclude(id=id)
        items=Items.filter(shop_id=promotion_combo.shop_id).filter(Q(main_product__in=shockdeals) |Q(promotion_combo__in=promotions))
        listitemdeal=[item.id for item in items]
        sameitem=list(set(listitemdeal).intersection(list_items))
        if len(sameitem)==0:
            promotion_combo.products.set([])
            promotion_combo.promotion_combo_name=request.data.get('promotion_combo_name')
            promotion_combo.valid_from=valid_from
            promotion_combo.valid_to=valid_to
            promotion_combo.combo_type=request.data.get('combo_type')
            promotion_combo.discount_percent=request.data.get('discount_percent')
            promotion_combo.discount_price=request.data.get('discount_price')
            promotion_combo.price_special_sale=request.data.get('price_special_sale')
            promotion_combo.limit_order=request.data.get('limit_order')
            promotion_combo.quantity_to_reduced=request.data.get('quantity_to_reduced')
            promotion_combo.save()
            promotion_combo.products.add(*list_items)
            data.update({'suscess':True})
        else:
            data.update({'error':True,'sameitem':sameitem})
        return Response(data)
    
class NewDeal(APIView):
    def get(self,request):
        shop=Shop.objects.get(user=request.user)
        deal_id=request.GET.get('deal_id')
        byproducts=request.GET.get('byprducts')
        mainproduct=request.GET.get('mainproducts')
        valid_to=request.GET.get('valid_to')
        valid_from=request.GET.get('valid_from')
        items=Item.objects.filter(shop=shop).order_by('-id')
        deal_shock=Buy_with_shock_deal.objects.get(id=deal_id)
        item_deal=deal_shock.main_products.all()
        list_id=[item.id for item in item_deal]
        items=items.exclude(id__in=list_id)
        if mainproducts:
            item_deal=deal_shock.byproducts.all()
            list_id=[item.id for item in item_deal]
            shockdeals=Buy_with_shock_deal.objects.filter(((Q(valid_from__lt=valid_from)&Q(valid_to__gt=valid_to)) | (Q(valid_from__gte=valid_from)&Q(valid_to__lte=valid_to)) | (Q(valid_from__lte=valid_from) & Q(valid_to__gt=valid_from)) | (Q(valid_from__gte=valid_from) & Q(valid_to__gte=valid_from)))  & Q(valid_to__gt=datetime.datetime.now())).exclude(id=id)
            promotions=Promotion_combo.objects.filter(((Q(valid_from__lt=valid_from)&Q(valid_to__gt=valid_to)) | (Q(valid_from__gte=valid_from)&Q(valid_to__lte=valid_to)) | (Q(valid_from__lte=valid_from) & Q(valid_to__gt=valid_from)) | (Q(valid_from__gte=valid_from) & Q(valid_to__gte=valid_from)))  & Q(valid_to__gt=datetime.datetime.now()))
            items=items.exclude(Q(id__in=list_id) |Q(main_product__in=shockdeals) |Q(promotion_combo__in=promotions))
        order=request.GET.get('order')
        price=request.GET.get('price')
        sort=request.GET.get('sort')
        name=request.GET.get('name')
        sku=request.GET.get('sku')
        item=request.GET.get('item')
        title=request.GET.get('title')
        q=request.GET.get('q')
        filteritem(price,sort,order,name,q,sku,item,items)
        data=ItemSellerSerializer(items,many=True).data
        return Response(data)
    def post(self,request):
        shop=Shop.objects.get(user=request.user)
        deal_shock,created=Buy_with_shock_deal.objects.get_or_create(
        shop=shop,
        shock_deal_type=request.data.get('shock_deal_type'),
        program_name_buy_with_shock_deal=request.data.get('program_name_buy_with_shock_deal'),
        valid_from=request.data.get('valid_from'),
        valid_to=request.data.get('valid_to'),
        limited_product_bundles=request.data.get('limited_product_bundles'),
        minimum_price_to_receive_gift=request.data.get('minimum_price_to_receive_gift'),
        number_gift=request.data.get('number_gift'),
        )
        data={
            'id':deal_shock.id
            }
        return Response(data)
    
class DetailDeal(APIView):
    def get(self,request,id):
        deal_shock=Buy_with_shock_deal.objects.get(id=id)
        data=BuywithsockdealSellerSerializer(deal_shock).data
        return Response(data)
    def post(self,request,id):
        deal_shock=Buy_with_shock_deal.objects.get(id=id)
        action=request.data.get('action')
        list_items=request.data.get('list_items')
        byproducts=request.data.get('byproducts')
        discount_model_list=request.data.get('discount_model_list')
        valid_from=request.data.get('valid_from')
        valid_to=request.data.get('valid_to')
        data={}
        if action=='change':
            deal_shock.program_name_buy_with_shock_deal=request.data.get('program_name_buy_with_shock_deal')
            deal_shock.valid_from=valid_from
            deal_shock.valid_to=valid_to
            deal_shock.limited_product_bundles=request.data.get('limited_product_bundles')
            deal_shock.minimum_price_to_receive_gift=request.data.get('minimum_price_to_receive_gift')
            deal_shock.number_gift=request.data.get('number_gift')
            deal_shock.save()
            data=BuywithsockdealinfoSerializer(deal_shock).data
        elif action=='savemain':
            shockdeals=Buy_with_shock_deal.objects.filter(((Q(valid_from__lt=valid_from)&Q(valid_to__gt=valid_to)) | (Q(valid_from__gte=valid_from)&Q(valid_to__lte=valid_to)) | (Q(valid_from__lte=valid_from) & Q(valid_to__gt=valid_from)) | (Q(valid_from__gte=valid_from) & Q(valid_to__gte=valid_from)))  & Q(valid_to__gt=datetime.datetime.now())).exclude(id=id)
            promotions=Promotion_combo.objects.filter(((Q(valid_from__lt=valid_from)&Q(valid_to__gt=valid_to)) | (Q(valid_from__gte=valid_from)&Q(valid_to__lte=valid_to)) | (Q(valid_from__lte=valid_from) & Q(valid_to__gt=valid_from)) | (Q(valid_from__gte=valid_from) & Q(valid_to__gte=valid_from)))  & Q(valid_to__gt=datetime.datetime.now()))
            items=Items.filter(shop_id=deal_shock.shop_id).filter(Q(main_product__in=shockdeals) |Q(promotion_combo__in=promotions))
            listitemdeal=[item.id for item in items]
            sameitem=list(set(listitemdeal).intersection(list_items))
            if len(sameitem)==0:
                deal_shock.main_products.set([])
                deal_shock.main_products.add(*list_items)
                data.update({'suscess':True})
            else:
                data.update({'error':True,'sameitem':sameitem})
        elif action=='addbyproduct':
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(byproducts)])
            list_byproducts=Item.objects.filter(id__in=byproducts).order_by(preserved)
            list_variation_deal=[]
            variations=Variation.objects.filter(item_id__in=byproducts)
            for variation in variations:
                if Variationdeal.objects.filter(deal_shock_id=id,item=variation.item,variation=variation).exists():
                    pass
                else:
                    list_variation_deal.append(Variationdeal(promotion_price=0,user_item_limit=0,deal_shock_id=id,item=variation.item,variation=variation))
            Variationdeal.objects.bulk_create(list_variation_deal)
            data=ByproductSellerSerializer(list_byproducts,many=True).data
        elif action=='savebyproduct':
            list_variation_deal=[]
            deal_shock.byproducts.set([])
            deal_shock.byproducts.add(*byproducts)
            for variation in discount_model_list:
                variationdeal=Variationdeal.objects.get(item_id=variation['item_id'],variation_id=variation['variation_id'],deal_shock_id=id)
                if variationdeal.promotion_price!=variation['promotion_price']:
                    variationdeal.promotion_price=variation['promotion_price']
                if variationdeal.user_item_limit!=variation['user_item_limit']:
                    variationdeal.user_item_limit=variation['user_item_limit']
                if variationdeal.enable!=variation['enable']:
                    variationdeal.enable=variation['enable']
                list_variation_deal.append(variationdeal)
            Variationdeal.objects.bulk_update(list_variation_deal, ['enable','promotion_price','user_item_limit'], batch_size=1000)
            data.update({'suscess':True})
        else:
            list_variation_deal=[]
            Variationdeal.objects.filter(deal_shock_id=id).exclude(item_id__in=byproducts).delete()
            deal_shock.active=True
            deal_shock.save()
            data.update({'suscess':True})
        return Response(data)

class NewprogramAPI(APIView):
    def get(self,request):
        shop=Shop.objects.get(user=request.user)
        program_id=request.GET.get('program_id')
        valid_to=request.GET.get('valid_to')
        valid_from=request.GET.get('valid_from')
        shop_programs=Shop_program.objects.filter(((Q(valid_from__lt=valid_from)&Q(valid_to__gt=valid_to)) | (Q(valid_from__gte=valid_from)&Q(valid_to__lte=valid_to)) | (Q(valid_from__lte=valid_from) & Q(valid_to__gt=valid_from)) | (Q(valid_from__gte=valid_from) & Q(valid_to__gte=valid_from)))  & Q(valid_to__gt=datetime.datetime.now()))
        if program_id:
            shop_programs=shop_programs.exclude(id=program_id)
        items=Item.objects.filter(shop=shop).exclude(shop_program__in=shop_programs).order_by('-id')
        order=request.GET.get('order')
        price=request.GET.get('price')
        sort=request.GET.get('sort')
        name=request.GET.get('name')
        sku=request.GET.get('sku')
        item=request.GET.get('item')
        title=request.GET.get('title')
        q=request.GET.get('q')
        filteritem(price, sort, order, name, q, sku, item, items)
        data=ItemSellerSerializer(items,many=True).data
        return Response(data) 
    def post(self,request): 
        shop=Shop.objects.get(user=request.user)
        name_program=request.data.get('name_program')
        valid_from=request.data.get('valid_from')
        valid_to=request.data.get('valid_to')
        list_items=request.data.get('list_items')
        action=request.data.get('action')
        discount_model_list=request.data.get('discount_model_list')
        data={}
        if action=='submit':
            shop_programs=Shop_program.objects.filter(((Q(valid_from__lt=valid_from)&Q(valid_to__gt=valid_to)) | (Q(valid_from__gte=valid_from)&Q(valid_to__lte=valid_to)) | (Q(valid_from__lte=valid_from) & Q(valid_to__gt=valid_from)) | (Q(valid_from__gte=valid_from) & Q(valid_to__gte=valid_from)))  & Q(valid_to__gt=datetime.datetime.now()))
            items=Item.objects.filter(shop=shop,shop_program__in=shop_programs)
            listitemprogram=[item.id for item in items]
            sameitem=list(set(listitemprogram).intersection(list_items))
            if len(sameitem)==0:
                shop_program,created=Shop_program.objects.get_or_create(
                        name_program=name_program,
                        valid_from=valid_from,
                        valid_to=valid_to,
                        shop=shop,
                        )
                shop_program.products.add(*list_items)
                listvariation=[Variation_discount(shop_program=shop_program,
                item_id=variation['item_id'],variation_id=variation['variation_id'],
                promotion_price=variation['promotion_price'],promotion_price_after_tax=variation['promotion_price'],
                enable=variation['enable'],
                user_item_limit=variation['user_item_limit'],promotion_stock=variation['promotion_stock']) for variation in discount_model_list]
                Variation_discount.objects.bulk_create(listvariation)
                data.update({'suscess':True})
            else:
                data.update({'error':True,'sameitem':sameitem})
        else:
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(list_items)])
            list_products=Item.objects.filter(id__in=list_items).order_by(preserved)
            data=ByproductSellerSerializer(list_products,many=True).data
        return Response(data)

class Detailprogram(APIView):
    def get(self,request,id):
        program=Shop_program.objects.get(id=id)
        data=ShopprogramSellerSerializer(program).data
        return Response(data)
    def post(self,request,id): 
        shop_program=Shop_program.objects.get(id=id)
        name_program=request.data.get('name_program')
        valid_from=request.data.get('valid_from')
        valid_to=request.data.get('valid_to')
        list_items=request.data.get('list_items')
        action=request.data.get('action')
        discount_model_list=request.data.get('discount_model_list')
        data={}
        if action=='submit':
            shop_programs=Shop_program.objects.filter(((Q(valid_from__lt=valid_from)&Q(valid_to__gt=valid_to)) | (Q(valid_from__gte=valid_from)&Q(valid_to__lte=valid_to)) | (Q(valid_from__lte=valid_from) & Q(valid_to__gt=valid_from)) | (Q(valid_from__gte=valid_from) & Q(valid_to__gte=valid_from)))  & Q(valid_to__gt=datetime.datetime.now())).exclude(id=id)
            items=Item.objects.filter(shop_id=shop_program.shop_id,shop_program__in=shop_programs)
            itemprogram=[item.id for item in items]
            sameitem=list(set(listitemprogram).intersection(list_items))
            if len(sameitem)==0:
                item_programs=shop_program.products.all()
                item_remove=item_programs.exclude(id__in=list_items)
                shop_program.name_program=name_program
                shop_program.valid_from=valid_from
                shop_program.valid_to=valid_to
                shop_program.save()
                Variation_discount.objects.filter(shop_program_id=id).exclude(item_id__in=list_items).delete()
                shop_program.products.set([])
                shop_program.products.add(*list_items)
                list_variation_update=[variation for variation in discount_model_list if variation.get('id')]
                list_variation=[Variation_discount(shop_program_id=id,
                item_id=variation['item_id'],variation_id=variation['variation_id'],
                promotion_price=variation['promotion_price'],
                promotion_price_after_tax=variation['promotion_price'],
                enable=variation['enable'],
                user_item_limit=variation['user_item_limit'],
                promotion_stock=variation['promotion_stock']) 
                for variation in discount_model_list if variation.get('id')==None]
                list_variation_updates=[]
                for variation in list_variation_update:
                    variation_discount=Variation_discount.objects.get(item_id=variation['item_id'],variation_id=variation['variation_id'],shop_program_id=id)
                    if variation_discount.promotion_price!=variation['promotion_price']:
                        variation_discount.promotion_price=variation['promotion_price']
                        variation_discount.promotion_price_after_tax=variation['promotion_price']
                    if variation_discount.promotion_stock!=variation['promotion_stock']:
                        variation_discount.promotion_stock=variation['promotion_stock']
                    if variation_discount.user_item_limit!=variation['user_item_limit']:
                        variation_discount.user_item_limit=variation['user_item_limit']
                    if variation_discount.enable!=variation['enable']:
                        variation_discount.enable=variation['enable']
                    
                list_variation_updates.append(variation_discount)
                Variation_discount.objects.bulk_create(list_variation)
                Variation_discount.objects.bulk_update(list_variation_updates, ['promotion_stock','promotion_price','user_item_limit','enable'], batch_size=1000)
                data.update({'suscess':True})
            else:
                data.update({'error':True,'sameitem':sameitem})
        else:
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(list_items)])
            list_products=Item.objects.filter(id__in=list_items).order_by(preserved)
            data=ByproductSellerSerializer(list_products,many=True).data
        return Response(data)
    
class Newflashsale(APIView):
    def get(self,request):
        shop=Shop.objects.get(user=request.user)
        order=request.GET.get('order')
        price=request.GET.get('price')
        sort=request.GET.get('sort')
        name=request.GET.get('name')
        sku=request.GET.get('sku')
        valid_to=request.GET.get('valid_to')
        valid_from=request.GET.get('valid_from')
        flash_sale_id=request.GET.get('flash_sale_id')
        item=request.GET.get('item')
        title=request.GET.get('title')
        q=request.GET.get('q')
        flash_sales=Flash_sale.objects.filter(((Q(valid_from__lt=valid_from)&Q(valid_to__gt=valid_to)) | (Q(valid_from__gte=valid_from)&Q(valid_to__lte=valid_to)) | (Q(valid_from__lte=valid_from) & Q(valid_to__gt=valid_from)) | (Q(valid_from__gte=valid_from) & Q(valid_to__gte=valid_from)))  & Q(valid_to__gt=datetime.datetime.now()))
        if flash_sale_id:
            flash_sales=flash_sales.exclude(id=flash_sale_id)
        items=Item.objects.filter(shop=shop).exclude(flash_sale__in=flash_sales).order_by('-id')
        filteritem(price, sort, order, name, q, sku, item, items)
        data=ItemSellerSerializer(items,many=True).data
        return Response(data) 
    def post(self,request):
        shop=Shop.objects.get(user=request.user)
        list_items=request.data.get('list_items')
        action=request.data.get('action')
        valid_to=request.data.get('valid_to')
        data={}
        if action=='submit': 
            flash_sales=Flash_sale.objects.filter(((Q(valid_from__lt=valid_from)&Q(valid_to__gt=valid_to)) | (Q(valid_from__gte=valid_from)&Q(valid_to__lte=valid_to)) | (Q(valid_from__lte=valid_from) & Q(valid_to__gt=valid_from)) | (Q(valid_from__gte=valid_from) & Q(valid_to__gte=valid_from)))  & Q(valid_to__gt=datetime.datetime.now()))
            items=Item.objects.filter(shop=shop,flash_sale__in=flash_sales)
            listitemflash=[item.id for item in items]
            sameitem=list(set(listitemflash).intersection(list_items))
            if len(sameitem)==0:
                discount_model_list=request.data.get('discount_model_list')
                flash_sale,created=Flash_sale.objects.get_or_create(
                        shop=shop,
                        valid_from=request.data.get('valid_from'),
                        valid_to=valid_to
                    )
                flash_sale.products.add(*list_items)
                listvariation=[Variationflashsale(flash_sale=flash_sale,
                item_id=variation['item_id'],variation_id=variation['variation_id'],
                promotion_price=variation['promotion_price'],
                enable=variation['enable'],
                user_item_limit=variation['user_item_limit'],
                promotion_stock=variation['promotion_stock']) for variation in discount_model_list]
                Variationflashsale.objects.bulk_create(listvariation)
                data.update({'suscess':True})
            else:
                data.update({'error':True,'sameitem':sameitem})

        else:
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(list_items)])
            list_products=Item.objects.filter(id__in=list_items).order_by(preserved)
            data=ByproductSellerSerializer(list_products,many=True).data
        return Response(data)
   
class DetailFlashsale(APIView):
    def get(self,request,id):
        flash_sale=Flash_sale.objects.get(id=id)
        data=FlashSaleSellerSerializer(flash_sale).data
        return Response(data)
    def post(self,request,id):
        flash_sale=Flash_sale.objects.get(id=id)
        list_items=request.data.get('list_items')
        action=request.data.get('action')
        valid_to=request.data.get('valid_to')
        data={}
        if action=='submit':
            flash_sales=Flash_sale.objects.filter(((Q(valid_from__lt=valid_from)&Q(valid_to__gt=valid_to)) | (Q(valid_from__gte=valid_from)&Q(valid_to__lte=valid_to)) | (Q(valid_from__lte=valid_from) & Q(valid_to__gt=valid_from)) | (Q(valid_from__gte=valid_from) & Q(valid_to__gte=valid_from)))  & Q(valid_to__gt=datetime.datetime.now())).exclude(id=id)
            items=Item.objects.filter(shop_id=flash_sale.shop_id,flash_sale__in=flash_sales)
            listitemflash=[item.id for item in items]
            sameitem=list(set(listitemflash).intersection(list_items))
            if len(sameitem)==0:
                discount_model_list=request.data.get('discount_model_list')
                item_flash_sale=flash_sale.products.all()
                item_remove=item_flash_sale.exclude(id__in=list_items)
                Variationflashsale.objects.filter(flash_sale_id=id).exclude(item_id__in=list_items).delete()
                flash_sale.valid_from=request.data.get('valid_from')
                flash_sale.valid_to=valid_to
                flash_sale.save()
                flash_sale.products.set([])
                flash_sale.products.add(*list_items)
                list_variation_update=[variation for variation in discount_model_list if variation.get('id')]
                listvariation=[Variationflashsale(flash_sale_id=id,
                item_id=variation['item_id'],variation_id=variation['variation_id'],
                promotion_price=variation['promotion_price'],
                enable=variation['enable'],
                user_item_limit=variation['user_item_limit'],
                promotion_stock=variation['promotion_stock']) for variation in discount_model_list if variation.get('id')==None]
                list_variation_updates=[]
                for variation in list_variation_update:
                    variation_flash_sale=Variationflashsale.objects.get(item_id=variation['item_id'],variation_id=variation['variation_id'],flash_sale_id=id)
                    if variation_flash_sale.promotion_price!=variation['promotion_price']:
                        variation_flash_sale.promotion_price=variation['promotion_price']
                    if variation_flash_sale.user_item_limit!=variation['user_item_limit']:
                        variation_flash_sale.user_item_limit=variation['user_item_limit']
                    if variation_flash_sale.promotion_stock!=variation['promotion_stock']:
                        variation_flash_sale.promotion_stock=variation['promotion_stock']
                    if variation_flash_sale.enable!=variation['enable']:
                        variation_flash_sale.enable=variation['enable']
                    list_variation_updates.append(variation_flash_sale)
                Variationflashsale.objects.bulk_create(listvariation)
                Variationflashsale.objects.bulk_update(list_variation_updates, ['promotion_stock','promotion_price','user_item_limit','enable'], batch_size=1000)
                data.update({'suscess':True})
            else:
                data.update({'error':True,'sameitem':sameitem})
        else:
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(list_items)])
            list_products=Item.objects.filter(id__in=list_items).order_by(preserved)
            data=ByproductSellerSerializer(list_products,many=True).data
        return Response(data)

@api_view(['GET', 'POST'])
def shipping(request):
    user=request.user
    shop=Shop.objects.get(user=user)
    if request.method=="POST":
        id=request.POST.get('id')
        shipping=Shipping.objects.get(id=id)
        if shipping in shop.shipping.all():
            shop.shipping.add(shipping)
        else:
            shop.shipping.add(shipping)
        data={'pb':'og'}
        return Response(data)
    else:
        list_shipping=Shipping.objects.all()
        list_shipping_shop=shop.shipping.all()
        list_shipping=[{'id':shipping.id,'method':shipping.method,'shipping_unit':shipping.shipping_unit,'enable':True if shipping in list_shipping_shop else False} for shipping in list_shipping]
        data={'list_shipping':list_shipping}
        return Response(data)
        
@api_view(['GET', 'POST'])
def get_shipping(request):
    user=request.user
    shop=Shop.objects.get(user=user)
    shipping_shop=shop.shipping.all()
    data={'shipping_shop':[{'id':i.id,'method':i.method,'unit':i.shipping_unit} for i in shipping_shop]}
    return Response(data)

@api_view(['GET', 'POST'])
def update_image(request):
    user=request.user
    shop=Shop.objects.get(user=user)
    if request.method=="POST":
        id=request.POST.get('id')
        delete=request.POST.get('delete')
        file=request.FILES.get('file')
        image_preview=request.FILES.get('file_preview')
        duration=request.POST.get('duration')
        if id and delete:
            UploadItem.objects.get(id=id).delete()
            data={'ob':'b'}
            return Response(data)
        elif id and file:
            uploaditem=UploadItem.objects.get(id=id)
            uploaditem.file=file
            uploaditem.save()
            data={
               'file':uploaditem.get_media()
            }
            return Response(data)
        else:
            uploaditem=UploadItem.objects.create(
                file=file,
                upload_by=shop,
                duration=duration,
                image_preview=image_preview
            )
            data={
                'id':uploaditem.id,'file':uploaditem.get_media(),'file_preview':uploaditem.file_preview(),
                'duration':uploaditem.duration
            }
            return Response(data)

@api_view(['GET', 'POST'])
def add_item(request):
    if request.method=='POST':
        user=request.user
        shop=Shop.objects.get(user=user)
        #item
        category_id=request.POST.get('category_id')
        from_quantity=request.POST.getlist('from_quantity')
        to_quantity=request.POST.getlist('to_quantity')
        price_range=request.POST.getlist('price_range')
       
        name=request.POST.get('name')
        description = request.POST.get('description')
        item = Item.objects.create(shop = shop,name = name,category_id=category_id,description=description)
        item.slug=re.sub('[,./\&]', "-",name) +  str(item.id)
        file_id=request.POST.getlist('file_id')
        file_id_remove=request.POST.getlist('file_id_remove')
        item.brand= request.POST.get('brand')
        item.weight=request.POST.get('weight')
        item.height=request.POST.get('height')
        item.length=request.POST.get('length')
        item.width=request.POST.get('width')
        item.save()
        BuyMoreDiscount.objects.bulk_create([
            BuyMoreDiscount(
               from_quantity=from_quantity[i],
               to_quantity=to_quantity[i],
               price=price_range[i],
               item=item
            )
            for i in range(len(from_quantity))
        ])

        shipping_method=request.POST.get('method')
        shipping=Shipping.objects.filter(method=shipping_method)
        list_upload=UploadItem.objects.filter(id__in=file_id)
        UploadItem.objects.filter(id__in=file_id_remove).delete()
        item.media_upload.add(*list_upload)
        item.shipping_choice.add(*shipping)
        detail_item=Detail_Item.objects.create(item=item)
        # clotes,jeans,pants,
        detail_item.brand_clothes=request.POST.get('brand_clothes')#skirt,dress
        detail_item.material=request.POST.get('material_clothes')#skirt
        detail_item.pants_length=request.POST.get('pants_length')#,dress
        detail_item.style=request.POST.get('style')#skirt,dress
        detail_item.sample=request.POST.get('sample')#skirt,dress
        detail_item.origin=request.POST.get('origin')#skirt,dress
        detail_item.pants_style=request.POST.get('pants_style')
        
        detail_item.petite=request.POST.get('CHOICE_YES_NO')#skirt,dress
        detail_item.season=request.POST.get('season')#skirt,dress
        detail_item.waist_version=request.POST.get('waist_version')#skirt,dress
        detail_item.very_big=request.POST.get('CHOICE_YES_NO')#skirt,dress
        #skirt
        detail_item.skirt_length=request.POST.get('skirt_length')#dress,
        detail_item.occasion=request.POST.get('clothes_occasion')#dress
        detail_item.dress_style=request.POST.get('dress_style')#dress
        #dress
        detail_item.collar=request.POST.get('clothes_collar')
        detail_item.sleeve_lenght=request.POST.get('sleeve_lenght')#T-shirt
        #Tanks & Camisoles
        detail_item.cropped_top=request.POST.get('CHOICE_YES_NO')
        detail_item.shirt_length=request.POST.get('shirt_length')
        #jean men
        detail_item.tallfit=request.POST.get('CHOICE_YES_NO')
        #woman
        #beaty
        detail_item.brand_beaty=request.POST.get('brand_beaty')
        detail_item.packing_type=request.POST.get('packing_tyle')
        detail_item.formula=request.POST.get('formula')
        detail_item.expiry=request.POST.get('expiry')
        detail_item.body_care=request.POST.get('body_care')
        detail_item.active_ingredients=request.POST.get('active_ingredients')
        detail_item.type_of_nutrition=request.POST.get('type_of_nutrition')
        detail_item.volume=request.POST.get('volume')
        detail_item.weight=request.POST.get('weight')
        #mobile
        detail_item.brand_mobile_gadgets=request.POST.get('brand_mobile_gadgets')
        detail_item.sim=request.POST.get('type_of_sim')
        detail_item.warranty_period=request.POST.get('warranty_period')
        detail_item.ram=request.POST.get('ram')
        detail_item.memory=request.POST.get('memory')
        detail_item.status=request.POST.get('Status')
        detail_item.warranty_type=request.POST.get('warranty_type')
        detail_item.processor=request.POST.get('processor')
        detail_item.screen=request.POST.get('screen')
        detail_item.phone_features=request.POST.get('phone_features')
        detail_item.operating_system=request.POST.get('operating_system')
        detail_item.telephone_cables=request.POST.get('telephone_cables')
        detail_item.main_camera=request.POST.get('main_camera')
        detail_item.camera_selfie=request.POST.get('camera_selfie')
        detail_item.number_of_sim_slots=request.POST.get('number_of_sim_slots'),
        detail_item.mobile_phone=request.POST.get('mobile_phone')
        detail_item.main_camera_number=request.POST.get('main_camera_number')
        #shoes mem
        detail_item.shoe_brand=request.POST.get('shoe_brand')
        detail_item.shoe_material=request.POST.get('shoe_material')
        detail_item.shoe_buckle_type=request.POST.get('shoe_buckle_type')
        detail_item.leather_outside=request.POST.get('leather_outside')
        detail_item.marker_style=request.POST.get('marker_style')
        detail_item.high_heel=request.POST.get('high_heel')
        detail_item.shoe_occasion=request.POST.get('shoe_occasion')
        detail_item.shoe_leather_type=request.POST.get('shoe_leather_type')
        shoe_collar_height=request.POST.get('shoe_collar_height')
        suitable_width=request.POST.get('CHOICE_YES_NO')

        #accessories
        detail_item.occasion_accessories=request.POST.get('occasion_accessories')
        detail_item.style_accessories=request.POST.get('style_accessories')
        #ring
        detail_item.accessory_set=request.POST.get('accessory_set')#
        
        #Household electrical appliances
        detail_item.brand_electrical=request.POST.get('brand_electrical')
        detail_item.receiver_type=request.POST.get('receiver_type')#

        #Travel & Luggage
        detail_item.brand_luggage=request.POST.get('brand_luggage')
        detail_item.material_luggage=request.POST.get('material_luggage')
        detail_item.waterproof=request.POST.get('CHOICE_YES_NO')
        detail_item.feature_folding_bag=request.POST.get('feature_folding_bag')
        #Computers & Laptops 
        #Desktop computer
        detail_item.storage_type=request.POST.get('storage_type')
        detail_item.optical_drive=request.POST.get('CHOICE_YES_NO')
        detail_item.port_interface=request.POST.get('port_interface')
        detail_item.processor_laptop=request.POST.get('processor_laptop')
        detail_item.number_of_cores=request.POST.get('number_of_cores')
        detail_item.dedicated_games=request.POST.get('CHOICE_YES_NO')
        detail_item.save()
        #size
        size_value=request.POST.getlist('size_value')
        size=Size.objects.bulk_create([
            Size(
                name=request.POST.get('size_name'),
                value=size_value[i])
            for i in range(len(size_value))
        ]
        )

        #color
        color_value=request.POST.getlist('color_value')
        color_image=request.FILES.getlist('color_image')
        none_color=[None for i in range(len(color_value))]
        
        for j in range(len(none_color)):
            for i in range(len(color_image)):
                if i==j:
                    none_color[j]=color_image[i]       
        color=Color.objects.bulk_create([
            Color(
            name=request.POST.get('color_name'),
            value=color_value[i],
            image=none_color[i])
            for i in range(len(color_value)) 
        ])

        none=[None]

        list_color=Color.objects.all().order_by('-id')[:len(color_value)]
        list_size=Size.objects.all().order_by('-id')[:len(size_value)]
        price=request.POST.getlist('price')
        inventory=request.POST.getlist('inventory')
        sku=request.POST.getlist('sku')
        variant_list =list(itertools.product(list_size,list_color))
        
        if len(list_color)==0 and len(list_size) > 0:
            variant_list=list(itertools.product(list_size,none))
        elif len(list_size)==0 and len(list_color) >0:
            variant_list=list(itertools.product(none,list_color))
        elif len(list_size) == 0 and len(list_color)==0:
            variant_list=list(itertools.product(none,none))
        
        # bulk_create() prohibited to prevent data loss due to unsaved related object 'color'. do chưa save từng thằng color
        size_variation=[]
        color_variation=[]
        for i,j in variant_list:
            size_variation.append(i),color_variation.append(j)
        variation_content=list(zip(size_variation,color_variation,price,inventory,sku))
        
        list_variation = [
            Variation(
            item=item,
            color=color,
            size=size,
            price=int(price),
            inventory=int(inventory),
            sku_classify=sku,
            ) 
            for size,color,price,inventory,sku in variation_content
        ]
        Variation.objects.bulk_create(list_variation)
        return Response({'product':'ok'})
    else:
        list_category=Category.objects.all()
        data={
            'list_category':[{'title':category.title,'id':category.id,'level':category.level,'choice':category.choice,
            'parent':category.getparent()} for category in list_category]
        } 
        return Response(data)

@api_view(['GET', 'POST'])
def update_item(request,id): 
    user=request.user
    shop=Shop.objects.get(user=user)
    item=Item.objects.get(id=id,shop=shop)
    if request.method=="POST":
        #item
        from_quantity=request.POST.getlist('from_quantity')
        to_quantity=request.POST.getlist('to_quantity')
        price_range=request.POST.getlist('price_range')
        BuyMoreDiscount.objects.bulk_create([
            BuyMoreDiscount(
               from_quantity=from_quantity[i],
               to_quantity=to_quantity[i],
               price=price_range[i],
               item_id=id
            )
            for i in range(len(from_quantity))
        ])
        
        name=request.POST.get('name')
        description = request.POST.get('description')
        item.slug=name + '.' + str(item.id)
        file_id=request.POST.getlist('file_id')
        file_id_remove=request.POST.getlist('file_id_remove')
        item.brand= request.POST.get('brand')
        item.weight=request.POST.get('weight')
        item.height=request.POST.get('height')
        item.length=request.POST.get('length')
        item.width=request.POST.get('width')
        from_quantity=request.POST.getlist('from_quantity')
        to_quantity=request.POST.getlist('to_quantity')
        price_range=request.POST.getlist('price_range')
        buy_more_id=request.POST.getlist('buy_more_id')
        # item 
        shipping_method=request.POST.getlist('method')
        item.brand= request.POST.get('brand')
        item.video=request.FILES.get('video')
        item.weight=request.POST.get('weigth')
        item.height=request.POST.get('height')
        item.length=request.POST.get('length')
        item.width=request.POST.get('width')
        
        #buy more
        
        shipping=Shipping.objects.filter(method=shipping_method)
        list_upload=UploadItem.objects.filter(id__in=file_id)
        UploadItem.objects.filter(id__in=file_id_remove).delete()
        item.media_upload.add(*list_upload)
        item.shipping_choice.add(*shipping)
        item.save()
        #detail item
        # clotes,jeans,pants,
        detail_item=Detail_Item.objects.get(item_id=item_id)
        detail_item.brand_clothes=request.POST.get('brand_clothes')#skirt,dress
        detail_item.material=request.POST.get('material_clothes')#skirt
        detail_item.pants_length=request.POST.get('pants_length')#,dress
        detail_item.style=request.POST.get('style')#skirt,dress
        detail_item.sample=request.POST.get('sample')#skirt,dress
        detail_item.origin=request.POST.get('origin')#skirt,dress
        detail_item.pants_style=request.POST.get('pants_style')
        
        detail_item.petite=request.POST.get('CHOICE_YES_NO')#skirt,dress
        detail_item.season=request.POST.get('season')#skirt,dress
        detail_item.waist_version=request.POST.get('waist_version')#skirt,dress
        detail_item.very_big=request.POST.get('CHOICE_YES_NO')#skirt,dress
        #skirt
        detail_item.skirt_length=request.POST.get('skirt_length')#dress,
        detail_item.occasion=request.POST.get('clothes_occasion')#dress
        detail_item.dress_style=request.POST.get('dress_style')#dress
        #dress
        detail_item.clothes_collar=request.POST.get('clothes_collar')
        detail_item.sleeve_lenght=request.POST.get('sleeve_lenght')#T-shirt
        #Tanks & Camisoles
        detail_item.cropped_top=request.POST.get('CHOICE_YES_NO')
        detail_item.shirt_length=request.POST.get('shirt_length')
        #jean men
        detail_item.tallfit=request.POST.get('CHOICE_YES_NO')
        #woman
        detail_item.pants_style=request.POST.get('pants_style_women')
        #beaty
        detail_item.brand_beaty=request.POST.get('brand_beaty')
        detail_item.packing_type=request.POST.get('packing_tyle')
        detail_item.formula=request.POST.get('formula')
        detail_item.expiry=request.POST.get('expiry')
        detail_item.body_care=request.POST.get('body_care')
        detail_item.active_ingredients=request.POST.get('active_ingredients')
        detail_item.type_of_nutrition=request.POST.get('type_of_nutrition')
        detail_item.volume=request.POST.get('volume')
        detail_item.weight=request.POST.get('weight')
        #mobile
        detail_item.brand_mobile_gadgets=request.POST.get('brand_mobile_gadgets')
        detail_item.sim=request.POST.get('type_of_sim')
        detail_item.warranty_period=request.POST.get('warranty_period')
        detail_item.ram=request.POST.get('ram')
        detail_item.memory=request.POST.get('memory')
        detail_item.status=request.POST.get('Status')
        detail_item.warranty_type=request.POST.get('warranty_type')
        detail_item.processor=request.POST.get('processor')
        detail_item.screen=request.POST.get('screen')
        detail_item.phone_features=request.POST.get('phone_features')
        detail_item.operating_system=request.POST.get('operating_system')
        detail_item.telephone_cables=request.POST.get('telephone_cables')
        detail_item.main_camera=request.POST.get('main_camera')
        detail_item.camera_selfie=request.POST.get('camera_selfie')
        detail_item.number_of_sim_slots=request.POST.get('number_of_sim_slots')
        detail_item.mobile_phone=request.POST.get('mobile_phone')
        detail_item.main_camera_number=request.POST.get('main_camera_number')
        #shoes mem
        detail_item.shoe_brand=request.POST.get('shoe_brand')
        detail_item.shoe_material=request.POST.get('shoe_material')
        detail_item.shoe_buckle_type=request.POST.get('shoe_buckle_type')
        detail_item.leather_outside=request.POST.get('leather_outside')
        detail_item.marker_style=request.POST.get('marker_style')
        detail_item.high_heel=request.POST.get('high_heel')
        detail_item.shoe_occasion=request.POST.get('shoe_occasion')
        detail_item.shoe_leather_type=request.POST.get('shoe_leather_type')
        detail_item.shoe_collar_height=request.POST.get('shoe_collar_height')
        detail_item.suitable_width=request.POST.get('CHOICE_YES_NO')

        #accessories
        detail_item.occasion_accessories=request.POST.get('occasion_accessories')
        detail_item.style_accessories=request.POST.get('style_accessories')
        #ring
        detail_item.accessory_set=request.POST.get('accessory_set')
        
        #Household electrical appliances
        detail_item.brand_electrical=request.POST.get('brand_electrical')
        detail_item.receiver_type=request.POST.get('receiver_type')

        #Travel & Luggage
        detail_item.brand_luggage=request.POST.get('brand_luggage')
        detail_item.material_luggage=request.POST.get('material_luggage')
        detail_item.waterproof=request.POST.get('CHOICE_YES_NO')
        detail_item.feature_folding_bag=request.POST.get('feature_folding_bag')
        #Computers & Laptops 
        #Desktop computer
        detail_item.storage_type=request.POST.get('storage_type')
        detail_item.optical_drive=request.POST.get('CHOICE_YES_NO')
        detail_item.port_interface=request.POST.get('port_interface')
        detail_item.processor_laptop=request.POST.get('processor_laptop')
        detail_item.number_of_cores=request.POST.get('number_of_cores')
        detail_item.dedicated_games=request.POST.get('CHOICE_YES_NO')
        detail_item.save()
        #size
        Variation.objects.filter(item=item).delete()
        size_value=request.POST.getlist('size_value')
        size=Size.objects.bulk_create([
            Size(
                name=request.POST.get('size_name'),
                value=size_value[i])
            for i in range(len(size_value))
        ])
        
        #color
        color_value=request.POST.getlist('color_value')
        color_image=request.FILES.getlist('color_image')
        none_color=[None for i in range(len(color_value))]
        for j in range(len(none_color)):
            for i in range(len(color_image)):
                if i==j:
                    none_color[j]=color_image[i]     

        color=Color.objects.bulk_create([
            Color(
            name=request.POST.get('color_name'),
            value=color_value[i],
            image=none_color[i])
            for i in range(len(color_value)) 
        ])

        none=[None]
        list_color=Color.objects.all().order_by('-id')[:len(color_value)]
        list_size=Size.objects.all().order_by('-id')[:len(size_value)]
        price=request.POST.getlist('price')
        inventory=request.POST.getlist('inventory')
        sku=request.POST.getlist('sku')
        variant_list =list(itertools.product(list_size,list_color))
        
        if len(list_color)==0 and len(list_size) > 0:
            variant_list=list(itertools.product(list_size,none))
        elif len(list_size)==0 and len(list_color) >0:
            variant_list=list(itertools.product(none,list_color))
        elif len(list_size) == 0 and len(list_color)==0:
            variant_list=list(itertools.product(none,none))
        
        # bulk_create() prohibited to prevent data loss due to unsaved related object 'color'. do chưa save từng thằng color
        size_variation=[]
        color_variation=[]
        for i,j in variant_list:
            size_variation.append(i),color_variation.append(j)
        variation_content=list(zip(size_variation,color_variation,price,inventory,sku))
        product_id_remove=request.POST.getlist('product_id_remove')
        Variation.objects.filter(id__in=product_id_remove).delete()
        list_variation = [
            Variation(
            item=item,
            color=color,
            size=size,
            price=int(price),
            inventory=int(inventory),
            sku_classify=sku,
            ) 
            for size,color,price,inventory,sku in variation_content
        ]
        Variation.objects.bulk_create(list_variation)
        Size.objects.filter(variation=None).delete()
        Color.objects.filter(variation=None).delete()
        return Response({'product':'ok'})
    else:
        list_color=Color.objects.filter(variation__item=item).distinct()
        detail_item=Detail_Item.objects.filter(item=item).values()
        buymore=BuyMoreDiscount.objects.filter(item_id=id)
        variations=Variation.objects.filter(item=item,size=None)
        list_variation=[{'value':color.value,'price':'','sku':'','inventory':'',
        'list_variation':[{'value':variation.size.value,'price':variation.price,'id':variation.id,
        'inventory':variation.inventory,'sku':variation.sku_classify} for variation in color.variation_set.all()]} for color in list_color]
        if variations.exists():
            list_variation=[{'id':variation.id,'value':variation.color.value,'price':variation.price,'sku':variation.sku_classify,'inventory':variation.inventory,
            'list_variation':[]} for variation in variations]
        shipping_shop=shop.shipping.all()
        shipping_item=item.shipping_choice.all()
        list_category_choice=item.category.get_ancestors(include_self=True)
        list_category=Category.objects.all()
        method=[{'method':i.method} for i in shipping_item]
        data={
        'buymore':buymore.values(),
        'item_info':{'name':item.name,'id':item.id, 'height':item.height,'length':item.length,'weight':item.weight,
        'description':item.description,'status':item.status,'sku_product':item.sku_product},
        'list_category_choice':[{'title':category.title,'id':category.id,'level':category.level,'choice':category.choice,
        'parent':category.getparent()} for category in list_category_choice],
        'list_category':[{'title':category.title,'id':category.id,'level':category.level,'choice':category.choice,
        'parent':category.getparent()} for category in list_category],
        'list_shipping_item':list({item['method']:item for item in method}.values()),
        'shipping_shop':shipping_shop.values(),
        'media_upload':[{'file':i.get_media(),'file_preview':i.file_preview(),
        'duration':i.duration,'filetype':i.media_type(),'id':i.id
        } for i in item.media_upload.all()],'list_size':item.get_size(),'list_color':item.get_list_color(),
        'item_detail':detail_item,'list_variation':list_variation}
        return Response(data)

@api_view(['GET', 'POST'])
def create_shop(request):
    user=request.user
    if request.method == "POST":
        profile=user.profile
        profile.user_type="S"
        profile.save()
        shop=Shop.objects.get(user=user)
        name=request.POST.get('name')
        shop.name =name
        shop.city = request.POST.get('city')
        shop.slug=name.replace(' ','')
        shop.save()
        data={'ok':'ok'}
        return Response(data)
    else:
        address=Address.objects.filter(user=user,address_type='B')
        data={'address':address.values(),'info':{'username':user.username,'email':user.email,'name':user.shop.name,'phone_number':str(user.profile.phone)}}
        return Response(data)
                    
import calendar
import pandas as pd
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
        cancel=request.GET.get('canceled')
        receive = request.GET.get('received')
        ordered=request.GET.get('ordered')
        accept=request.GET.get('accepted')
        canceled=False
        if cancel:
            canceled=True
        accepted=[False,True]
        ordered=True
        if accept:
            accepted=[True]
        received=[False,True]
        if receive:
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




   


