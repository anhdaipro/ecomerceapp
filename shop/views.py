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

from slugify import slugify

from django.shortcuts import render, redirect
from django.contrib import messages
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
import json
from buyer.serializers import (OrdersellerSerializer,ItemSellerSerializer,
VariationSerializer,
CategorySellerSerializer,

VoucherSerializer,
VouchersellerSerializer,
ShopProgramSerializer,
ShopprogramSellerSerializer,
ByproductSellerSerializer,
BuywithsockdealSerializer,
BuywithsockdealSellerSerializer,
ComboSerializer,
ItemappSerializer,
CombosellerSerializer,
BuywithsockdealinfoSerializer,
FlashSaleSerializer,
ReviewshopSerializer,
FlashSaleSellerSerializer,
VariationsellerSerializer,
ItemproductSerializer,
ShopAwardinfoSerializer,
ShopAwardSerializer,
ShopAwardDetailSerializer,
FollowOfferdetailSerializer,
FollowOfferInfoSerializer,
FollowOfferSerializer,
)
import pytz
timezones = pytz.timezone('Asia/Ho_Chi_Minh')
now=datetime.datetime.now(tz=timezones)
class ListvoucherAPI(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = VoucherSerializer
    def get(self,request):
        choice=request.GET.get('choice')
        offset=request.GET.get('offset')
        start_day=request.GET.get('start_day')
        end_day=request.GET.get('end_day')
        name=request.GET.get('name')
        name=request.GET.get('name')
        shop=Shop.objects.get(user=request.user)
        vouchers=Voucher.objects.filter(shop=shop,valid_from__gte=(now-timedelta(days=200))).prefetch_related('products').prefetch_related('order_voucher')
        if start_day:
            vouchers=vocuhers.filter(valid_from__gte=start_day)
        if end_day:
            vouchers=vocuhers.filter(valid_to__lte=end_day)
        if choice:
            if choice=='current':
                vouchers=vouchers.filter(valid_from__lt=timezone.now(),valid_to__gt=timezone.now())
            elif choice=='upcoming':
                vouchers=vouchers.filter(valid_from__gt=timezone.now())
            else:
                vouchers=vouchers.filter(valid_to__lt=timezone.now())
        count=vouchers.count()
        from_item=0
        if offset:
            from_item=int(offset)
        to_item=from_item+5
        if from_item+5>=count:
            to_item=count
        vouchers=vouchers[from_item:to_item]
        return Response({'data':VoucherSerializer(vouchers,many=True).data,'count':count})

class ListcomboAPI(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ComboSerializer
    def get(self,request):
        choice=request.GET.get('choice')
        offset=request.GET.get('offset')
        shop=Shop.objects.get(user=request.user)
        promotions=Promotion_combo.objects.filter(shop=shop,valid_from__gte=(now-timedelta(days=200))).prefetch_related('products__media_upload')
        option=request.GET.get('option')
        keyword=request.GET.get('keyword')
        if option and keyword:
            if option=='2':
                promotions=promotions.filter(products__name__istartswith=keyword)
            elif option=='3':
                promotions=promotions.filter(products__sku_product=keyword)
            else:
                promotions=promotions.filter(promotion_combo_name__istartswith=keyword)
        if choice:
            if choice=='current':
                promotions=promotions.filter(valid_from__lt=timezone.now(),valid_to__gt=timezone.now())
            elif choice=='upcoming':
                promotions=promotions.filter(valid_from__gt=timezone.now())
            else:
                promotions=promotions.filter(valid_to__lt=timezone.now())
        start_day=request.GET.get('start_day')
        end_day=request.GET.get('end_day')
        if start_day:
            promotions=promotions.filter(valid_from__gte=start_day)
        if end_day:
            promotions=promotions.filter(valid_to__lte=end_day)
        count=promotions.count()
        from_item=0
        if offset:
            from_item=int(offset)
        to_item=from_item+5
        if from_item+5>=count:
            to_item=count
        promotions=promotions[from_item:to_item]
        return Response({'data':ComboSerializer(promotions,many=True).data,'count':count})

class ListdealshockAPI(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = BuywithsockdealSerializer
    def get(self,request):
        shop=Shop.objects.get(user=request.user)
        deal_shocks=Buy_with_shock_deal.objects.filter(shop=shop,valid_from__gte=(now-timedelta(days=200))).prefetch_related('main_products__media_upload').prefetch_related('byproducts__media_upload')
        choice=request.GET.get('choice')
        offset=request.GET.get('offset')
        start_day=request.GET.get('start_day')
        end_day=request.GET.get('end_day')
        option=request.GET.get('option')
        keyword=request.GET.get('keyword')
        deal_type=request.GET('deal_type')
        if option and keyword:
            if option=='2':
                deal_shocks=deal_shocks.filter(main_products__name__istartswith=keyword)
            elif option=='3':
                deal_shocks=deal_shocks.filter(main_products__sku_product=keyword)
            else:
                deal_shocks=deal_shocks.filter(program_name_buy_with_shock_deal__istartswith=keyword)
        if start_day:
            deal_shocks=deal_shocks.filter(valid_from__gte=start_day)
        if end_day:
            deal_shocks=deal_shocks.filter(valid_to__lte=end_day)
        if deal_type:
            deal_shocks=deal_shocks.filter(shock_deal_type=deal_type)
        if choice:
            if choice=='current':
                deal_shocks=deal_shocks.filter(valid_from__lt=timezone.now(),valid_to__gt=timezone.now())
            elif choice=='upcoming':
                deal_shocks=deal_shocks.filter(valid_from__gt=timezone.now())
            else:
                deal_shocks=deal_shocks.filter(valid_to__lt=timezone.now())
        count=deal_shocks.count()
        from_item=0
        if offset:
            from_item=int(offset)
        to_item=from_item+5
        if from_item+5>=count:
            to_item=count
        deal_shocks=deal_shocks[from_item:to_item]
        return Response({'data':BuywithsockdealSerializer(deal_shocks,many=True).data,'count':count})
       
class ListFollowOfferAPI(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request):
        choice=request.GET.get('choice')
        offset=request.GET.get('offset')
        shop=Shop.objects.get(user=request.user)
        follow_offers=Follower_offer.objects.filter(shop=shop,valid_from__gte=(now-timedelta(days=200))).prefetch_related('follower_offder').order_by('-id')
        if choice:
            if choice=='current':
                follow_offers=follow_offers.filter(valid_from__lt=timezone.now(),valid_to__gt=timezone.now())
            elif choice=='upcoming':
                follow_offers=follow_offers.filter(valid_from__gt=timezone.now())
            else:
                follow_offers=follow_offers.filter(valid_to__lt=timezone.now())
        start_day=request.GET.get('start_day')
        end_day=request.GET.get('end_day')
        if start_day:
            follow_offers=follow_offers.filter(valid_from__gte=start_day)
        if end_day:
            follow_offers=follow_offers.filter(valid_to__lte=end_day)
        count=follow_offers.count()
        from_item=0
        if offset:
            from_item=int(offset)
        to_item=from_item+5
        if from_item+5>=count:
            to_item=count
        follow_offers=follow_offers[from_item:to_item]
        return Response({'data':FollowOfferSerializer(follow_offers,many=True).data,'count':count})

class ListShopAwardAPI(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request):
        choice=request.GET.get('choice')
        offset=request.GET.get('offset')
        shop=Shop.objects.get(user=request.user)
        shop_awards=Shop_award.objects.filter(shop=shop,valid_from__gte=(now-timedelta(days=200))).prefetch_related('award_shop_award').order_by('-id')
        if choice:
            if choice=='current':
                shop_awards=shop_awards.filter(valid_from__lt=timezone.now(),valid_to__gt=timezone.now())
            elif choice=='upcoming':
                shop_awards=shop_awards.filter(valid_from__gt=timezone.now())
            else:
                shop_awards=shop_awards.filter(valid_to__lt=timezone.now())
        start_day=request.GET.get('start_day')
        end_day=request.GET.get('end_day')
        if start_day:
            shop_awards=shop_awards.filter(valid_from__gte=start_day)
        if end_day:
            shop_awards=shop_awards.filter(valid_to__lte=end_day)
        count=shop_awards.count()
        from_item=0
        if offset:
            from_item=int(offset)
        to_item=from_item+5
        if from_item+5>=count:
            to_item=count
        shop_awards=shop_awards[from_item:to_item]
        return Response({'data':ShopAwardSerializer(shop_awards,many=True).data,'count':count})

class ListprogramAPI(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ShopProgramSerializer
    def get(self,request):
        shop=Shop.objects.get(user=request.user)
        choice=request.GET.get('choice')
        offset=request.GET.get('offset')
        programs=Shop_program.objects.filter(shop=shop,valid_from__gte=(now-timedelta(days=200))).prefetch_related('products__media_upload').order_by('-id')
        option=request.GET.get('option')
        keyword=request.GET.get('keyword')
        if option and keyword:
            if option=='1':
                programs=programs.filter(name_program__istartswith=keyword)
            elif option=='2':
                programs=programs.filter(products__name__istartswith=keyword)
            else:
                programs=programs.filter(products__sku_product=keyword)
        if choice:
            if choice=='current':
                programs=programs.filter(valid_from__lt=timezone.now(),valid_to__gt=timezone.now())
            elif choice=='upcoming':
                programs=programs.filter(valid_from__gt=timezone.now())
            else:
                programs=programs.filter(valid_to__lt=timezone.now())
        start_day=request.GET.get('start_day')
        end_day=request.GET.get('end_day')
        if start_day:
            programs=programs.filter(valid_from__gte=start_day)
        if end_day:
            programs=programs.filter(valid_to__lte=end_day)
        count=programs.count()
        from_item=0
        if offset:
            from_item=int(offset)
        to_item=from_item+5
        if from_item+5>=count:
            to_item=count
        programs=programs[from_item:to_item]
        return Response({'data':ShopProgramSerializer(programs,many=True).data,'count':count})

class ListflashsaleAPI(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = FlashSaleSerializer
    def get(self,request):
        choice=request.GET.get('choice')
        offset=request.GET.get('offset')
        shop=Shop.objects.get(user=request.user)
        flash_sales=Flash_sale.objects.filter(shop=shop,valid_from__gte=(now-timedelta(days=200))).prefetch_related('products__media_upload').order_by('-id')
        
        if choice:
            if choice=='current':
                flash_sales=flash_sales.filter(valid_from__lt=timezone.now(),valid_to__gt=timezone.now())
            elif choice=='upcoming':
                flash_sales=flash_sales.filter(valid_from__gt=timezone.now())
            else:
                flash_sales=flash_sales.filter(valid_to__lt=timezone.now())
        start_day=request.GET.get('start_day')
        end_day=request.GET.get('end_day')
        if start_day:
            flash_sales=flash_sales.filter(valid_from__gte=start_day)
        if end_day:
            flash_sales=flash_sales.filter(valid_to__lte=end_day)
        count=flash_sales.count()
        from_item=0
        if offset:
            from_item=int(offset)
        to_item=from_item+5
        if from_item+5>=count:
            to_item=count
        flash_sales=flash_sales[from_item:to_item]
        return Response({'data':FlashSaleSerializer(flash_sales,many=True).data,'count':count})
    
class ShopprofileAPIView(APIView):
    permission_classes = (IsAuthenticated,)
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
        name=request.data.get('name')
        description=request.data.get('description')
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
    current_date=now
    count_order_waiting_comfirmed=Order.objects.filter(shop=shop,ordered=True,canceled=False,accepted=False,being_delivered=False,received=False,accepted_date__gt=timezone.now()).count()
    count_order_canceled=Order.objects.filter(shop=shop,ordered=True,canceled=True).count()
    count_order_processed=Order.objects.filter(shop=shop,ordered=True,canceled=False,accepted=True,received=False,being_delivered=False).count()
    count_order_waiting_processed=Order.objects.filter(shop=shop,ordered=True,being_delivered=False,accepted=False,accepted_date__lt=timezone.now()).count()
    total_order_day=Order.objects.filter(shop=shop,ordered=True,ordered_date__gte=current_date).annotate(day=TruncHour('ordered_date')).values('day').annotate(count=Count('id')).values('day','count')
    total_amount_day=Order.objects.filter(shop=shop,ordered=True,ordered_date__gte=current_date).annotate(day=TruncHour('ordered_date')).values('day').annotate(sum=Sum('amount')).values('day','sum')

    data={
    'count_order_waiting_comfirmed':count_order_waiting_comfirmed,
    'count_order_canceled':count_order_canceled,'count_order_processed':count_order_processed,
    'count_order_waiting_processed':count_order_waiting_processed
    }
    return Response(data)

class Updateorder(APIView):
    def post(self,request):
        orders=request.data.get('orders')
        Order.objects.filter(id__in=orders).update(accepted=True,accepted_date=timezone.now())
        return Response({'success':True})
class Listordershop(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request):
        shop=Shop.objects.get(user=request.user)
        orders=Order.objects.filter(shop=shop,ordered=True).prefetch_related('items__item__media_upload').prefetch_related('items__item__promotion_combo').prefetch_related('items__item__byproduct').prefetch_related('items__item__shop_program').prefetch_related('items__product__color').prefetch_related('items__product__size').prefetch_related('items__byproduct_cart')
        type_order=request.GET.get('type')
        source=request.GET.get('source')
        if type_order:
            if type_order=='unpaid':
                orders=orders.filter(accepted=False,being_delivered=False,received=False,canceled=False)
            if type_order=='toship':
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
        id=request.data.get('id')
        status=request.data.get('status')
        user=request.user
        shop=Shop.objects.get(user=user)
        order=Order.objects.get(id=id,shop=shop)
        if status=='1':
            order.accepted=True
            order.accepted_date=timezone.now()
        elif status=='2':
            order.being_delivered=True
            order.shipping_start_date=timezone.now()
        elif status=='3':
            order.received=True
            order.received_date=timezone.now()
        order.save()
        return Response({'success':True})

class ShopratingAPI(APIView):
    def get(self,request):
        shop=Shop.objects.get(user=request.user)
        list_review=ReView.objects.filter(cartitem__shop=shop).distinct()
        page=request.GET.get('page')
        review_rating=request.GET.get('review_rating')
        page_size=request.GET.get('page_size')
        start_day=request.GET.get('start_day')
        end_day=request.GET.get('end_day')
        username=request.GET.get('username')
        name_product=request.GET.get('name_product')
        category_id=request.GET.get('category_id')
        if category_id:
            category=Category.objects.get(id=category)
            list_review=list_review.filter(cartitem__item__category=category)
        if name_product:
            list_review=list_review.filter(cartitem__item__name__istartswith=name_product)
        if username:
            list_review=list_review.filter(user__username__istartswith=username)
        if review_rating:
            list_review=list_review.filter(review_rating=review_rating)
        if start_day:
            list_review=list_review.filter(created__gte=start_day)
        if end_day:
            list_review=list_review.filter(created__lte=end_day)
        paginator = Paginator(list_review,page_size)
        page_obj = paginator.get_page(page)
        data={'averge_review':shop.averge_review(),'reviews':ReviewshopSerializer(page_obj,many=True).data,'page_count':paginator.num_pages}
        return Response(data) 
    def post(self,request):
        text=request.data.get('text')
        id=request.data.get('id')
        review=ReView.objects.get(id=id)
        reply=Reply.objects.create(text=text,review=review,user=request.user)
        data={'id':reply.id,'text':reply.text}
        return Response(data)

class Updatevariation(APIView):
    def get(self,request):
        item_id=request.GET.get('item_id')
        listvariation=Variation.objects.filter(item_id=item_id)
        data=VariationSerializer(listvariation,many=True).data
        return Response(data)
    def post(self,request):
        variations=request.data.get('variations')
        list_variation=[]
        for item in variations:
            variation=Variation.objects.get(id=item['variation_id'])
            if variation.price!=item['price']:
                variation.price=item['price']
            if variation.inventory!=item['inventory']:
                variation.inventory=item['inventory']
            list_variation.append(variation)
        Variation.objects.bulk_update(list_variation,['price','inventory'])
        return Response({'success':True})
class Listproduct(APIView):
    def get(self,request):
        user=request.user
        shop=Shop.objects.get(user=user)
        items=Item.objects.filter(shop=shop)
        offset=request.GET.get('offset')
        count=items.count()
        from_item=0
        if offset:
            from_item=int(offset)
        to_item=from_item+10
        if from_item+10>=count:
            to_item=count
        items=items[from_item:to_item]
        return Response({'products':ItemappSerializer(items,many=True).data,'count':count})
        
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
        item_id=request.data.get('items')
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
        item_id=request.data.get('items')
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
        item_id=request.data.get('items')
        Item.objects.filter(id__in=item_id).delete()
        product=Item.objects.filter(shop=shop)
        page_no=request.data.get('page_no')
        per_page=request.data.get('per_page')
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
        shop=Shop.objects.get(user=request.user)
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
        vocher=Voucher.objects.create(
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
        data=VouchersellerSerializer(voucher).data
        return Response(data)
    def post(self,request,id):
        shop=Shop.objects.get(user=request.user)
        voucher=Voucher.objects.get(id=id)
        action=request.data.get('action')
        if action=='delete':
            voucher.delete()
        else:
            items=Item.objects.filter(shop=shop)
            list_items=request.data.get('list_items')
            voucher.code_type=request.data.get('code_type')
            voucher.products.set([])
            voucher.name_of_the_discount_program=request.data.get('name_of_the_discount_program')
            voucher.code = request.data.get('code')
            voucher.valid_from=request.data.get('valid_from')
            voucher.valid_to=request.data.get('valid_to')
            voucher.discount_type=request.data.get('discount_type')
            voucher.amount = request.data.get('amount')
            voucher.percent = request.data.get('percent')
            voucher.maximum_usage=request.data.get('maximum_usage')
            voucher.voucher_type=request.data.get('voucher_type')
            voucher.maximum_discount=request.data.get('maximum_discount')
            voucher.minimum_order_value=request.data.get('minimum_order_value')
            voucher.setting_display=request.data.get('setting_display')
            voucher.save()
            if voucher.code_type=="All":
                voucher.products.add(*items)
            else:
                voucher.products.add(*list_items)
        data={'success':True }
        return Response(data)

class GameAPI(APIView):
    def post(self,id):
        shop_award=Shop_award.objects.get(id=id)
        award=request.data.get('award')
        gammers=Gammer.objects.filter(user=request.user,created__gte=timezone.now())
        if gammers.count()<4:
            Gammer.objects.create(user=request.user,shop_award_id=id,award_id=award['id'])
        data={'success':True}
        return Response(data)

class NewShopAwardAPI(APIView):
    def post(self,request):
        shop=Shop.objects.get(user=request.user)
        valid_from=request.data.get("valid_from")
        valid_to=request.data.get("valid_to")
        action=request.data.get("action")
        shop_awards=Shop_award.objects.filter((Q(valid_from__gte=valid_from)&Q(valid_from__lte=valid_to)) |(Q(valid_to__gte=valid_from)&Q(valid_to__lte=valid_to)))
        data={}
        if shop_awards.exists():
            data.update({'error':True})
        else:
            data.update({'suscess':True})
            if action=='submit':
                list_award=request.data.get('list_award')
                shop_award=Shop_award.objects.create(
                    shop=shop,
                    game_name=request.data.get("game_name"),
                    valid_from=valid_from,
                    valid_to=valid_to
                )
                Award.objects.bulk_create([Award(
                minimum_order_value=award['minimum_order_value'],
                maximum_discount=award['maximum_discount'] if award['maximum_discount']!='' else 0,
                quantity=award['quantity'],
                shop_award=shop_award,
                amount=award['amount'] if award['amount']!='' else 0,
                percent=award['percent'] if award['percent']!='' else 0,
                discount_type=award['discount_type'],
                type_award=award['type_award'],
                type_voucher='Offer') for award in list_award])
            
        return Response(data)

class DetailShopAwardAPI(APIView):
    def post(self,request,id):
        shop=Shop.objects.get(user=request.user)
        shop_award=Shop_award.objects.get(id=id)
        valid_from=request.data.get("valid_from")
        valid_to=request.data.get("valid_to")
        action=request.data.get("action")
        shop_awards=Shop_award.objects.filter((Q(valid_from__gte=valid_from)&Q(valid_from__lte=valid_to)) |(Q(valid_to__gte=valid_from)&Q(valid_to__lte=valid_to))).exclude(id=id)
        data={}
        if action=='delete':
            shop_award.delete()
            data.update({'suscess':True})
        else:
            if shop_awards.exists():
                data.update({'error':True})
            else:
                data.update({'suscess':True})
                if action=='submit':
                    list_award=request.data.get('list_award')
                    list_award_update=[award for award in list_award if award['id']]
                    list_awards=[]
                    for award in list_award_update:
                        award_update=Award.objects.get(id=award['id'])
                        if award_update.minimum_order_value!=award['minimum_order_value']:
                            award_update.minimum_order_value=award['minimum_order_value']
                        if award_update.maximum_discount!=award['maximum_discount']:
                            award_update.maximum_discount=award['maximum_discount']
                        if award_update.quantity!=quantity['quantity']:
                            award_update.quantity=award['quantity']
                        if award_update.amount!=quantity['amount']:
                            award_update.amount=award['amount']
                        if award_update.percent!=quantity['percent']:
                            award_update.percent=award['percent']
                        if award_update.discount_type!=quantity['discount_type']:
                            award_update.discount_type=award['discount_type']
                        list_awards.append(award_update)
                    
                    shop_award.game_name=request.data.get("game_name")
                    shop_award.valid_from=valid_from
                    shop_award.valid_to=valid_to
                    shop_award.save()
                    Award.objects.bulk_create([Award(
                    minimum_order_value=award['minimum_order_value'],
                    maximum_discount=award['maximum_discount'],
                    quantity=award['quantity'],
                    amount=award['amount'] if award['amount']!='' else 0,
                    percent=award['percent'] if award['percent']!='' else 0,
                    discount_type=award['discount_type'],
                    type_award=award['type_award'],
                    type_voucher='Offer') for award in list_award if award['id']==None])
                    Award.objects.bulk_update(award_update, ['minimum_order_value','maximum_discount',
                        'quantity','amount','percent','discount_type'], batch_size=1000)
        return Response(data)
    def get(self,request,id):
        shop_award=Shop_award.objects.get(id=id)
        return Response(ShopAwardDetailSerializer(shop_award).data)

class NewFollowOffer(APIView):
    def post(self,request):
        shop=Shop.objects.get(user=request.user)
        valid_from=request.data.get("valid_from")
        valid_to=request.data.get("valid_to")
        action=request.data.get("action")
        follower_offers=Follower_offer.objects.filter((Q(valid_from__gte=valid_from)&Q(valid_from__lte=valid_to)) |(Q(valid_to__gte=valid_from)&Q(valid_to__lte=valid_to)))
        data={}
        if follower_offers.exists():
            data.update({'error':True})
        else:
            data.update({'suscess':True})
            if action=='submit':
                offer_follow=Follower_offer.objects.create(
                shop=shop,
                offer_name=request.data.get('offer_name'),
                valid_from=valid_from,
                valid_to=valid_to,
                discount_type=request.data.get('discount_type'),
                amount = request.data.get('amount'),
                percent = request.data.get('percent'),
                maximum_usage=request.data.get('maximum_usage'),
                type_offer="Voucher",
                voucher_type=request.data.get('voucher_type'),
                maximum_discount=request.data.get('maximum_discount'),
                minimum_order_value=request.data.get('minimum_order_value'),
            )
        return Response(data)

class DetailFollowOffer(APIView):
    def get(self,request,id):
        offer_follow=Follower_offer.objects.get(id=id)
        return Response(FollowOfferDetailSerializer(offer_follow).data)
    def post(self,request,id):
        shop=Shop.objects.get(user=request.user)
        offer_follow=Follower_offer.objects.get(id=id)
        valid_from=request.data.get("valid_from")
        valid_to=request.data.get("valid_to")
        action=request.data.get("action")
        follower_offers=Follower_offer.objects.filter((Q(valid_from__gte=valid_from)&Q(valid_from__lte=valid_to)) |(Q(valid_to__gte=valid_from)&Q(valid_to__lte=valid_to))).exclude(id=id)
        data={}
        if action=='delete':
            offer_follow.delete()
            data.update({'suscess':True})
        else:
            if follower_offers.exists():
                data.update({'error':True})
            else:
                data.update({'suscess':True})
                if action=='submit':
                    offer_follow.offer_name=request.data.get('offer_name')
                    offer_follow.valid_from=valid_from
                    offer_follow.valid_to=valid_to
                    offer_follow.discount_type=request.data.get('discount_type')
                    offer_follow.amount = request.data.get('amount')
                    offer_follow.percent = request.data.get('percent')
                    offer_follow.maximum_usage=request.data.get('maximum_usage')
                    offer_follow.maximum_discount=request.data.get('maximum_discount')
                    offer_follow.minimum_order_value=request.data.get('minimum_order_value')
                    offer_follow.save()

        return Response(data)
    
class NewcomboAPI(APIView):
    def get(self,request):
        shop=Shop.objects.get(user=request.user)
        valid_to=request.GET.get('valid_to')
        combo_id=request.GET.get('combo_id')
        valid_from=request.GET.get('valid_from')
        shockdeals=Buy_with_shock_deal.objects.filter((Q(valid_from__gte=valid_from)&Q(valid_from__lte=valid_to)) |(Q(valid_to__gte=valid_from)&Q(valid_to__lte=valid_to)))
        promotions=Promotion_combo.objects.filter((Q(valid_from__gte=valid_from)&Q(valid_from__lte=valid_to)) |(Q(valid_to__gte=valid_from)&Q(valid_to__lte=valid_to)))
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
        action=request.data.get('action')
        valid_to=request.data.get('valid_to')
        list_items=request.data.get('list_items')
        shockdeals=Buy_with_shock_deal.objects.filter((Q(valid_from__gte=valid_from)&Q(valid_from__lte=valid_to)) |(Q(valid_to__gte=valid_from)&Q(valid_to__lte=valid_to)))
        promotions=Promotion_combo.objects.filter((Q(valid_from__gte=valid_from)&Q(valid_from__lte=valid_to)) |(Q(valid_to__gte=valid_from)&Q(valid_to__lte=valid_to)))
        items=Item.objects.filter(shop=shop).filter(Q(main_product__in=shockdeals) |Q(promotion_combo__in=promotions))
        listitemdeal=[item.id for item in items]
        data={}
        sameitem=list(set(listitemdeal).intersection(list_items))
        if len(sameitem)==0:
            if action=='submit':
                promotion_combo=Promotion_combo.objects.create(
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
        action=request.data.get('action')
        promotion_combo=Promotion_combo.objects.get(id=id)
        data={}
        shockdeals=Buy_with_shock_deal.objects.filter((Q(valid_from__gte=valid_from)&Q(valid_from__lte=valid_to)) |(Q(valid_to__gte=valid_from)&Q(valid_to__lte=valid_to)))
        promotions=Promotion_combo.objects.filter((Q(valid_from__gte=valid_from)&Q(valid_from__lte=valid_to)) |(Q(valid_to__gte=valid_from)&Q(valid_to__lte=valid_to))).exclude(id=id)
        items=Item.objects.filter(shop_id=promotion_combo.shop_id).filter(Q(main_product__in=shockdeals) |Q(promotion_combo__in=promotions))
        listitemdeal=[item.id for item in items]
        sameitem=list(set(listitemdeal).intersection(list_items))
        if action=='delete':
            promotion_combo.delete()
            data.update({'suscess':True})
        else:
            if (promotion_combo.valid_from<now and promotion_combo.valid_to>now) or len(sameitem)>0:
                data.update({'error':True,'sameitem':sameitem})
            else:
                if action=='submit':
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
            
        return Response(data)
    
class NewDeal(APIView):
    def get(self,request):
        shop=Shop.objects.get(user=request.user)
        deal_id=request.GET.get('deal_id')
        byproducts=request.GET.get('byprducts')
        mainproducts=request.GET.get('mainproducts')
        valid_to=request.GET.get('valid_to')
        valid_from=request.GET.get('valid_from')
        items=Item.objects.filter(shop=shop).order_by('-id')
        if deal_id:
            deal_shock=Buy_with_shock_deal.objects.get(id=deal_id)
            item_deal=deal_shock.main_products.all()
            list_id=[item.id for item in item_deal]
            items=items.exclude(id__in=list_id)
        if mainproducts:
            item_deal=deal_shock.byproducts.all()
            list_id=[item.id for item in item_deal]
            shockdeals=Buy_with_shock_deal.objects.filter((Q(valid_from__gte=valid_from)&Q(valid_from__lte=valid_to)) |(Q(valid_to__gte=valid_from)&Q(valid_to__lte=valid_to))).exclude(id=deal_id)
            promotions=Promotion_combo.objects.filter((Q(valid_from__gte=valid_from)&Q(valid_from__lte=valid_to)) |(Q(valid_to__gte=valid_from)&Q(valid_to__lte=valid_to)))
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
        deal_shock=Buy_with_shock_deal.objects.create(
        shop=shop,
        shock_deal_type=request.data.get('shock_deal_type'),
        program_name_buy_with_shock_deal=request.data.get('program_name_buy_with_shock_deal'),
        valid_from=request.data.get('valid_from'),
        valid_to=request.data.get('valid_to'),
        limited_product_bundles=request.data.get('limited_product_bundles'),
        minimum_price_to_receive_gift=request.data.get('minimum_price_to_receive_gift'),
        number_gift=request.data.get('number_gift'),
        )
        gift=request.data.get('gift')
        if gift:
            deal_shock.active=True
            deal_shock.variations=discount_model_list
            deal_shock.save()
            discount_model_list=request.data.get('discount_model_list',[])
            list_variation_deal=[]
            deal_shock.byproducts.set([])
            deal_shock.byproducts.add(*byproducts)
            
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
        now=timezone.now()
        data={}
        if action=='delete':
            deal_shock.delete()
            data.update({'suscess':True})
        else:
            list_items=request.data.get('list_items')
            byproducts=request.data.get('byproducts')
            discount_model_list=request.data.get('discount_model_list')
            valid_from=request.data.get('valid_from')
            valid_to=request.data.get('valid_to')
            if action=='change':
                deal_shock.program_name_buy_with_shock_deal=request.data.get('program_name_buy_with_shock_deal')
                deal_shock.valid_from=valid_from
                deal_shock.valid_to=valid_to
                deal_shock.limited_product_bundles=request.data.get('limited_product_bundles')
                deal_shock.minimum_price_to_receive_gift=request.data.get('minimum_price_to_receive_gift')
                deal_shock.number_gift=request.data.get('number_gift')
                deal_shock.save()
                data=BuywithsockdealinfoSerializer(deal_shock).data
            elif action=='addbyproduct':
                preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(byproducts)])
                list_byproducts=Item.objects.filter(id__in=byproducts).order_by(preserved)
                data=ByproductSellerSerializer(list_byproducts,many=True).data
            elif action=='savebyproduct':
                list_variation_deal=[]
                deal_shock.byproducts.set([])
                deal_shock.variations=discount_model_list
                deal_shock.byproducts.add(*byproducts)
                
                data.update({'suscess':True})
            elif action=='submit':
                list_variation_deal=[]
                Variationdeal.objects.filter(deal_shock_id=id).exclude(item_id__in=byproducts).delete()
                deal_shock.active=True
                deal_shock.save()
                data.update({'suscess':True})
            else:
                shockdeals=Buy_with_shock_deal.objects.filter((Q(valid_from__gte=valid_from)&Q(valid_from__lte=valid_to)) |(Q(valid_to__gte=valid_from)&Q(valid_to__lte=valid_to))).exclude(id=id)
                promotions=Promotion_combo.objects.filter((Q(valid_from__gte=valid_from)&Q(valid_from__lte=valid_to)) |(Q(valid_to__gte=valid_from)&Q(valid_to__lte=valid_to)))
                items=Item.objects.filter(shop_id=deal_shock.shop_id).filter(Q(main_product__in=shockdeals) |Q(promotion_combo__in=promotions))
                listitemdeal=[item.id for item in items]
                sameitem=list(set(listitemdeal).intersection(list_items))
                if (deal_shock.valid_to>now and deal_shock.valid_from<now) or len(sameitem)>0:
                    data.update({'error':True,'sameitem':sameitem})
                else:
                    if action=='savemain':
                        deal_shock.main_products.set([])
                        deal_shock.main_products.add(*list_items)
                        data.update({'suscess':True})
        return Response(data)

class NewprogramAPI(APIView):
    def get(self,request):
        shop=Shop.objects.get(user=request.user)
        program_id=request.GET.get('program_id')
        valid_to=request.GET.get('valid_to')
        valid_from=request.GET.get('valid_from')
        shop_programs=Shop_program.objects.filter((Q(valid_from__gte=valid_from)&Q(valid_from__lte=valid_to)) |(Q(valid_to__gte=valid_from)&Q(valid_to__lte=valid_to)))
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
        if action=='addproduct':
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(list_items)])
            list_products=Item.objects.filter(id__in=list_items).order_by(preserved)
            data=ByproductSellerSerializer(list_products,many=True).data
        else:
            shop_programs=Shop_program.objects.filter((Q(valid_from__gte=valid_from)&Q(valid_from__lte=valid_to)) |(Q(valid_to__gte=valid_from)&Q(valid_to__lte=valid_to)))
            items=Item.objects.filter(shop=shop,shop_program__in=shop_programs)
            listitemprogram=[item.id for item in items]
            sameitem=list(set(listitemprogram).intersection(list_items))
            if len(sameitem)==0:
                data.update({'suscess':True})
                if action=='submit':
                    shop_program=Shop_program.objects.create(
                            name_program=name_program,
                            valid_from=valid_from,
                            valid_to=valid_to,
                            shop=shop,
                            variations=discount_model_list
                            )
                    shop_program.products.add(*list_items)
                    
            else:
                data.update({'error':True,'sameitem':sameitem})
            
        return Response(data)
class Createcategory(APIView):
    def post(self,request):
        categories=request.data.get('categories')
        parent_id=request.data.get('parent_id')
        
        list_categories=[]
        for category in categories:
            list_categories.append(Category(title=category['title'],level=0,lft=0,rght=0,tree_id=0,parent_id=parent_id,choice=category['choice']))

        Category.objects.bulk_create(list_categories)
        Category.objects.rebuild()
        return Response({'success':True})
class Detailprogram(APIView):
    def get(self,request,id):
        program=Shop_program.objects.get(id=id)
        data=ShopprogramSellerSerializer(program).data
        return Response(data)
    def post(self,request,id): 
        shop_program=Shop_program.objects.get(id=id)
        action=request.data.get('action')
        data={}
        if action=='delete':
            shop_program.delete()
            data.update({'suscess':True})
        else:
            name_program=request.data.get('name_program')
            valid_from=request.data.get('valid_from')
            valid_to=request.data.get('valid_to')
            list_items=request.data.get('list_items')
            discount_model_list=request.data.get('discount_model_list')
            if action=='addproduct':
                preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(list_items)])
                list_products=Item.objects.filter(id__in=list_items).order_by(preserved)
                data=ByproductSellerSerializer(list_products,many=True).data
            
            else:
                shop_programs=Shop_program.objects.filter((Q(valid_from__gte=valid_from)&Q(valid_from__lte=valid_to)) |(Q(valid_to__gte=valid_from)&Q(valid_to__lte=valid_to))).exclude(id=id)
                items=Item.objects.filter(shop_id=shop_program.shop_id,shop_program__in=shop_programs)
                listitemprogram=[item.id for item in items]
                sameitem=list(set(listitemprogram).intersection(list_items))
                if (shop_program.valid_from<now and shop_program.valid_to>now) or len(sameitem)>0:
                    data.update({'error':True,'sameitem':sameitem})
                else:
                    data.update({'suscess':True})
                    if action=='submit':
                        item_programs=shop_program.products.all()
                        item_remove=item_programs.exclude(id__in=list_items)
                        shop_program.name_program=name_program
                        shop_program.valid_from=valid_from
                        shop_program.valid_to=valid_to
                        shop_program.variations=discount_model_list
                        shop_program.save()
                        
                        shop_program.products.set([])
                        shop_program.products.add(*list_items)
                        
        
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
        flash_sales=Flash_sale.objects.filter((Q(valid_from=valid_from)&Q(valid_to=valid_to)) & Q(valid_to__gt=now))
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
        valid_from=request.data.get('valid_from')
        data={}
        if action=='addproduct':
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(list_items)])
            list_products=Item.objects.filter(id__in=list_items).order_by(preserved)
            data=ByproductSellerSerializer(list_products,many=True).data
        else:
            flash_sales=Flash_sale.objects.filter(shop=shop).filter((Q(valid_from=valid_from)&Q(valid_to=valid_to))  & Q(valid_to__gt=now))
            if flash_sales.exists():
                data.update({'error':True})
            else:
                data.update({'suscess':True})
                if action=='submit': 
                    discount_model_list=request.data.get('discount_model_list')
                    flash_sale=Flash_sale.objects.create(
                            shop=shop,
                            valid_from=valid_from,
                            variations=discount_model_list,
                            valid_to=valid_to
                        )
                    flash_sale.products.add(*list_items)
                    
            
        return Response(data)

def turn_on(item):
    variation=item
    variation['enable']=True
    return variation
def turn_off(item):
    variation=item
    variation['enable']=False
    return variation
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
        valid_from=request.data.get('valid_from')
        data={}
        if action=='delete':
            flash_sale.delete()
            data.update({'suscess':True})
        else:
            if action=='addproduct':
                preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(list_items)])
                list_products=Item.objects.filter(id__in=list_items).order_by(preserved)
                data=ByproductSellerSerializer(list_products,many=True).data
            elif action=='turn_on':
                variations = map(turn_on,list(flash_sale.variations))
                flash_sale.variations=list(variations)
                flash_sale.save()
            elif action=='turn_off':
                variations = map(turn_off,list(flash_sale.variations))
                flash_sale.variations=list(variations)
                flash_sale.save()
            else:
                flash_sales=Flash_sale.objects.filter(shop_id=flash_sale.shop_id).filter((Q(valid_from=valid_from)&Q(valid_to=valid_to))  & Q(valid_to__gt=now)).exclude(id=id)
                if flash_sales.exists():
                    data.update({'error':True})
                else:
                    data.update({'suscess':True})
                    if action=='submit':
                        discount_model_list=request.data.get('discount_model_list')
                        item_flash_sale=flash_sale.products.all()
                        item_remove=item_flash_sale.exclude(id__in=list_items)
                        flash_sale.valid_from=valid_from
                        flash_sale.valid_to=valid_to
                        flash_sale.variations=discount_model_list
                        flash_sale.save()
                        flash_sale.products.set([])
                        flash_sale.products.add(*list_items)
                    
        return Response(data)

@api_view(['GET', 'POST'])
def shipping(request):
    user=request.user
    shop=Shop.objects.get(user=user)
    if request.method=="POST":
        id=request.data.get('id')
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
    data={'shipping_shop': shipping_shop.values()}
    return Response(data)

@api_view(['GET', 'POST'])
def update_image(request):
    user=request.user
    shop=Shop.objects.get(user=user)
    if request.method=="POST":
        id=request.data.get('id')
        delete=request.data.get('delete')
        file=request.FILES.get('file')
        image_preview=request.FILES.get('file_preview')
        duration=request.data.get('duration')
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

class NewItem(APIView):
    def post(self,request):
        user=request.user
        shop=Shop.objects.get(user=user)
        #item
        category_id=request.data.get('category_id')
        name=request.data.get('name')
        description = request.data.get('description')
        info_detail=request.data.get('info_detail')
        item = Item.objects.create(shop = shop,name = name,category_id=category_id,description=description)
        item.slug=slugify(name) + '.' + str(item.id)
        files=request.data.get('files',[])
        item.detail=info_detail
        item.brand= request.data.get('brand')
        item.weight=request.data.get('weight')
        height=request.data.get('height')
        length=request.data.get('length')
        width=request.data.get('width')
        if height:
            item.height=height
        if length:
            item.length=length
        if width:
            item.width=width
        item.save()
        buymorediscounts=request.data.get('buymorediscounts',[])
        BuyMoreDiscount.objects.bulk_create([
            BuyMoreDiscount(
               from_quantity=item['from_quantity'],
               to_quantity=item['to_quantity'],
               price=item['price_range'],
               item=item
            )
            for item in buymorediscounts
        ])
        shipping_method=request.data.get('method',[])
        shipping=Shipping.objects.filter(method__in=shipping_method)
        list_upload=UploadItem.objects.filter(id__in=files)
        
        item.media_upload.add(*list_upload)
        item.shipping_choice.add(*shipping)
        variations=request.data.get('variations')
        list_variation = [
            Variation(
            item=item,
            color_id=variation['color_id'],
            size_id=variation['size_id'],
            price=variation['price'],
            inventory=variation['inventory'],
            sku_classify=variation['sku_classify'],
            ) 
            for variation in variations
        ]
        Variation.objects.bulk_create(list_variation)
        return Response({'success':True})
    def get(self,request):
        list_category=Category.objects.all()
        data={
            'list_category':CategorySellerSerializer(list_category,many=True).data

        } 
        return Response(data)

class Createclassify(APIView):
    def post(self,request):
        sizes=request.POST.get('sizes')
        sizes=json.loads(sizes)
        size_name=request.POST.get('size_name')
        sizes_create=[obj for obj in sizes if type(obj['id'])!=int]
        sizes_update=[obj for obj in sizes if type(obj['id'])==int]
        list_size_update=[]
        for item in sizes_update:
            size=Size.objects.get(id=item['id'])
            size.name=size_name
            size.value=item['value']
            list_size_update.append(size)
        Size.objects.bulk_update(list_size_update,['value','name'])

        sizes=Size.objects.bulk_create([
            Size(
                name=size_name,
                value=size['value'])
            for size in sizes_create
        ])
        #color
        value_update=request.POST.getlist('value_update')
        image_update=request.FILES.getlist('image_update')
        value=request.POST.getlist('value')
        image=request.FILES.getlist('image')
        color_id=request.POST.getlist('color_id')
        color_name=request.POST.get('color_name')
        colors_create=[None for i in range(len(value))]
        colors_update=[None for i in range(len(value_update))]
        for j in range(len(colors_update)):
            for i in range(len(image_update)):
                if i==j:
                    colors_update[j]=image_update[i] 
        for j in range(len(colors_create)):
            for i in range(len(image)):
                if i==j:
                    colors_create[j]=image[i]    

        colors=Color.objects.bulk_create([
            Color(
            name=color_name,
            value=value[i],
            image=colors_create[i])
            for i in range(len(value)) 
        ])
        list_color_update=[]
        for i in range(len(value_update)):
            color=Color.objects.get(id=color_id[i])
            if colors_update[i]:
                color.image=colors_update[i]
            color.name=color_name
            color.value=value_update[i]
            list_color_update.append(color)
        Color.objects.bulk_update(list_color_update,['name','value','image'])
        return Response({'colors':[{'id':color.id,'value':color.value} for color in colors],'sizes':[{'id':size.id,'value':size.value} for size in sizes]})

class UpdateclassifyAPI(APIView):
    def post(self,reuquest):
        sizes=request.POST.get('sizes')
        sizes_create=[obj for obj in sizes if type(obj['id'])!=int]
        sizes_update=[obj for obj in sizes if type(obj['id'])==int]
        Size.objects.bulk_update([
            Size(
                name=request.POST.get('size_name'),
                value=size['value'])
            for size in sizes_update
        ],['value','name'])

        #color
        color_value=request.POST.getlist('color_value')
        color_image=request.FILES.getlist('color_image')
        color_id=request.POST.getlist('color_id')
        none_color=[None for i in range(len(color_value))]
        list_color=[]
        for j in range(len(none_color)):
            for i in range(len(color_image)):
                if i==j:
                    none_color[j]=color_image[i]     
        for i in range(len(color_value)):
            color=Color.objects.get(id=color_id[i])
            color.value=color_value[i]
            color.name=request.POST.get('color_name')
            if color_image[i]:
                color.image=color_image[i]
            list_color.append(color)
        Color.objects.bulk_update(list_color,['image','name','value'])


class Updateitem(APIView):
    def get(self,request,id):
        user=request.user
        shop=Shop.objects.get(user=user)
        item=Item.objects.get(id=id,shop=shop)
        list_color=Color.objects.filter(variation__item=item).distinct()
        buymore=BuyMoreDiscount.objects.filter(item_id=id)
        variations=Variation.objects.filter(item=item)
        
        variations=[{'variation_id':variation.id,'color_value':variation.get_color(),'size_value':variation.get_size(),
        'color_id':variation.color_id,'size_id':variation.size_id,'price':variation.price,'sku_classify':variation.sku_classify,'inventory':variation.inventory,
        } for variation in variations]
        shipping_shop=shop.shipping.all()
        shipping_item=item.shipping_choice.all()

        list_category_choice=item.category.get_ancestors(include_self=True)
        list_category=Category.objects.all()

        list_id_choice=item.category.get_full_id()
        list_category_choice=Category.objects.filter(id__in=list_id_choice)

        method=[{'method':i.method} for i in shipping_item]
        data={
        'buymore':buymore.values(),
        'item_info':{'name':item.name,'id':item.id,'width':item.width,'height':item.height,'length':item.length,'weight':item.weight,
        'description':item.description,'status':item.status,'sku_product':item.sku_product,'info_detail':item.detail},

        'list_category_choice':[{'title':category.title,'id':category.id,'level':category.level,'choice':category.choice,
        'parent':category.getparent()} for category in list_category_choice],

        'list_category_choice':CategorySellerSerializer(list_category_choice,many=True).data,

        'list_shipping_item':list({item['method']:item for item in method}.values()),
        'shipping_shop':shipping_shop.values(),
        'media_upload':[{'file':i.get_media(),'file_preview':i.file_preview(),
        'duration':i.duration,'filetype':i.media_type(),'id':i.id
        } for i in item.media_upload.all()],'sizes':item.get_list_size(),'colors':item.get_list_color(),
        'item_detail':item.detail,'variations':variations}
        return Response(data)
    def post(self,request,id): 
        user=request.user
        shop=Shop.objects.get(user=user)
        item=Item.objects.get(id=id,shop=shop)
        action=request.data.get('action')
        data={}
        #item
        if action=='hidden':
            Item.objects.filter(id=id).update(hidden=True)
            data.update({'success':True})
        elif action=='delete':
            Item.objects.filter(id=id).delete()
            data.update({'success':True})
        elif action=='violet':
            data.update({'success':True})
            Item.objects.filter(id=id).update(violet=True)
        elif action=='update':
            buymorediscounts=request.data.get('buymorediscounts',[])
            buymore_remain=request.data.get('buymorediscounts_remain',[])
            BuyMoreDiscount.objects.filter(item_id=id).exclude(id__in=buymore_remain).delete()
            BuyMoreDiscount.objects.bulk_create([
                BuyMoreDiscount(
                from_quantity=item['from_quantity'],
                to_quantity=item['to_quantity'],
                price=item['price_range'],
                item_id=id
                )
                for item in buymorediscounts if type(item['id'])!=int
            ])
            list_buymore_update=[]
            for item in buymorediscounts:
                if type(item['id'])==int:
                    buymorediscount=BuyMoreDiscount.objects.get(id=item['id'])
                    buymorediscount.from_quantity=item['from_quantity']
                    buymorediscount.to_quantity=item['to_quantity']
                    buymorediscount.price=item['price_range']
                    list_buymore_update.append(buymorediscount)
            BuyMoreDiscount.objects.bulk_update(list_buymore_update,['from_quantity','to_quantity','price'])
            name=request.data.get('name')
            description = request.data.get('description')
            info_detail=request.data.get('info_detail')
            item.detail=info_detail
            item.slug=slugify(name) + '.' + str(item.id)
            files=request.data.get('files',[])
            UploadItem.objects.filter(Q(media_upload=item) &~Q(id__in=files)).delete()
            item.brand= request.data.get('brand')
            item.weight=request.data.get('weight')
            height=request.data.get('height')
            length=request.data.get('length')
            width=request.data.get('width')
            if height:
                item.height=height
            if length:
                item.length=length
            if width:
                item.width=width
            # item 
            shipping_method=request.data.get('method',[])
            item.brand= request.data.get('brand')
            
            item.height=request.data.get('height')
            item.length=request.data.get('length')
            item.width=request.data.get('width')
        
            #buy more

            shipping=Shipping.objects.filter(method__in=shipping_method)
            list_upload=UploadItem.objects.filter(id__in=files)
            
            item.media_upload.add(*list_upload)
            item.shipping_choice.add(*shipping)
            item.save()
           
           
            #size
            list_update=[]
            variations=request.data.get('variations',[])
            variations_remain=request.data.get('variations_remain',[])
            Variation.objects.filter(item_id=id).exclude(id__in=variations_remain).delete()
            for item in variations:
                if type(item['variation_id'])==int:
                    variation=Variation.objects.get(id=item['variation_id'])
                    if item['price']!=variation.price:
                        variation.price=item['price']
                    if item['inventory']!=variation.inventory:
                        variation.inventory=item['inventory']
                    if item['sku_classify']:
                        variation.sku=item['sku_classify']
                    list_update.append(variation)
            Variation.objects.bulk_update(list_update,['inventory','price','sku_classify'])
            list_variation = [
            Variation(
            item=item,
            color_id=variation['color_id'],
            size_id=variation['size_id'],
            price=variation['price'],
            inventory=variation['inventory'],
            sku_classify=variation['sku_classify'],
            ) 
            for variation in variations if type(variation['variation_id'])!=int
            ]
            Variation.objects.bulk_create(list_variation)

            data.update({'succes':True})
        return Response(data)
    

@api_view(['GET', 'POST'])
def create_shop(request):
    user=request.user
    if request.method == "POST":
        profile=user.profile
        profile.user_type="S"
        profile.save()
        shop=Shop.objects.get(user=user)
        name=request.data.get('name')
        shop.name =name
        shop.city = request.data.get('city')
        shop.slug=name.replace(' ','')
        shop.save()
        data={'ok':'ok'}
        return Response(data)
    else:
        address=Address.objects.filter(user=user,address_type='B')
        data={'address':address.values(),'info':{'username':user.username,'email':user.email,'name':user.shop.name,'phone_number':str(user.profile.phone)}}
        return Response(data)              


