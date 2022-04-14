
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
from category.models import *
from checkout.models import *
from discount.models import *
from cart.models import *
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
from .serializers import VoucherSerializer,ComboSerializer,ProgramSerializer,DealsockSerializer,FlashsaleSerializer

class ListvoucherAPI(ListAPIView):
    
    serializer_class = VoucherSerializer
    def get_queryset(self):
        request = self.request
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token_obj = AccessToken(token)
        user_id=access_token_obj['user_id']
        user=User.objects.get(id=user_id)
        shop=Shop.objects.get(user=user)
        return Vocher.objects.filter(shop=shop)

class ListcomboAPI(ListAPIView):
    
    serializer_class = ComboSerializer
    def get_queryset(self):
        request = self.request
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token_obj = AccessToken(token)
        user_id=access_token_obj['user_id']
        user=User.objects.get(id=user_id)
        shop=Shop.objects.get(user=user)
        return Promotion_combo.objects.filter(shop=shop)

class ListdealshockAPI(ListAPIView):
    
    serializer_class = DealsockSerializer
    def get_queryset(self):
        request = self.request
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token_obj = AccessToken(token)
        user_id=access_token_obj['user_id']
        user=User.objects.get(id=user_id)
        shop=Shop.objects.get(user=user)
        return Buy_with_shock_deal.objects.filter(shop=shop)

class ListprogramAPI(ListAPIView):
    
    serializer_class = ProgramSerializer
    def get_queryset(self):
        request = self.request
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token_obj = AccessToken(token)
        user_id=access_token_obj['user_id']
        user=User.objects.get(id=user_id)
        shop=Shop.objects.get(user=user)
        return Shop_program.objects.filter(shop=shop)

class ListflashsaleAPI(ListAPIView):
    
    serializer_class = FlashsaleSerializer
    def get_queryset(self):
        request = self.request
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token_obj = AccessToken(token)
        user_id=access_token_obj['user_id']
        user=User.objects.get(id=user_id)
        shop=Shop.objects.get(user=user)
        return Flashsale.objects.filter(shop=shop)
    
@api_view(['GET', 'POST'])
def index(request):
    shop=Shop.objects.get(user=user)
    current_date=datetime.datetime.now()
    orders = Order.objects.filter(shop=shop,ordered=True,received=True)
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
    'hours':hours,'sum_hour':sum_hour,'count_hour':count_hour,'current_date':current_date, 
    'shop_name':shop.name,'logo':shop.logo.url
    }
    return Response(data)
    
@api_view(['GET', 'POST'])
def product(request):
    shop=Shop.objects.get(user=user)
    product=Item.objects.filter(shop=shop)
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
            'count_product':product.count()
        }
        return Response(data)
    else:
        if item_id:
            item=Item.objects.get(id=item_id)
            variation=Variation.objects.filter(item=item).order_by('-color__value')[3:]
            list_variation=[{'number_order':i.number_order(),'inventory':i.inventory,'price':i.price,'sku':i.sku_classify,'color_value':i.color.value,'size_value':i.size.value
                } for i in variation]
            data={'a':list_variation,'count_variation':variation.count()}
            return Response(data)
        elif page_no:
            obj_paginator = Paginator(product, per_page)
            first_page = obj_paginator.get_page(page_no)
            variation=Variation.objects.filter(item__in=first_page).order_by('-color__value')
            list_product=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),
                'id':i.id,'item_sku':i.sku_product,'get_absolute_id':i.get_absolute_id()
                } for i in first_page]
            list_variation=[{'number_order':i.number_order(),'inventory':i.inventory,'price':i.price,'sku':i.sku_classify,'color_value':i.get_color(),'size_value':i.get_size(),
            'item__id':i.item.id ,'id':i.id
                    } for i in variation]
            data={
                'a':list_product,'b':list_variation,'page_range':obj_paginator.num_pages,'count_product':product.count()
            }
            return Response(data)
        elif price and sort:
            if sort == "sort-asc":
                product=product.order_by('variation__price').distinct()
            else:
                product=product.order_by('-variation__price').distinct()
            obj_paginator = Paginator(product, per_page)
            first_page = obj_paginator.get_page(1)
            variation=Variation.objects.filter(item__in=first_page).order_by('-color__value')
            list_product=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),
                'id':i.id,'item_sku':i.sku_product,'get_absolute_id':i.get_absolute_id()
                } for i in first_page]
            list_variation=[{'number_order':i.number_order(),'inventory':i.inventory,'price':i.price,'sku':i.sku_classify,'color_value':i.get_color(),'size_value':i.get_size(),
            'item__id':i.item.id ,'id':i.id
                    } for i in variation]
            data={
                'a':list_product,'b':list_variation,'page_range':obj_paginator.num_pages,'count_product':product.count()
            }
            return Response(data)
        elif order and sort:
            if sort == "sort-asc":
                product=product.annotate(count=Count('variation__orderitem__order__id')).order_by('count')
            else:
                product=product.annotate(count=Count('variation__orderitem__order__id')).order_by('-count')
            obj_paginator = Paginator(product, per_page)
            first_page = obj_paginator.get_page(1)
            variation=Variation.objects.filter(item__in=first_page).order_by('-color__value')
            list_product=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),
                'id':i.id,'item_sku':i.sku_product,'get_absolute_id':i.get_absolute_id()
                } for i in first_page]
            list_variation=[{'number_order':i.number_order(),'inventory':i.inventory,'price':i.price,'sku':i.sku_classify,'color_value':i.get_color(),'size_value':i.get_size(),
            'item__id':i.item.id ,'id':i.id
                    } for i in variation]
            data={
                'a':list_product,'b':list_variation,'page_range':obj_paginator.num_pages,'count_product':product.count()
            }
            return Response(data)
        elif inventory and sort:
            if sort == "sort-asc":
                product=product.order_by('variation__inventory').distinct()
            else:
                product=product.order_by('-variation__inventory').distinct()
            obj_paginator = Paginator(product, per_page)
            first_page = obj_paginator.get_page(1)
            variation=Variation.objects.filter(item__in=first_page).order_by('-color__value')
            list_product=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),
                'id':i.id,'item_sku':i.sku_product,'get_absolute_id':i.get_absolute_id()
                } for i in first_page]
            list_variation=[{'number_order':i.number_order(),'inventory':i.inventory,'price':i.price,'sku':i.sku_classify,'color_value':i.get_color(),'size_value':i.get_size(),
            'item__id':i.item.id ,'id':i.id
                    } for i in variation]
            data={
                'a':list_product,'b':list_variation,'page_range':obj_paginator.num_pages,'count_product':product.count()
            }
            return Response(data)

@api_view(['GET', 'POST'])
def get_product(request):
    token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
    access_token_obj = AccessToken(token)
    user_id=access_token_obj['user_id']
    user=User.objects.get(id=user_id)
    shop=Shop.objects.get(user=user)
    page=1
    pagesize=12
    list_product=Item.objects.filter(shop=shop)
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
            data={
                'list_variation':[{'variation_id':variation.id,'color_value':variation.get_color(),
                'size_value':variation.get_size(),'inventory':variation.inventory,
                'discount':variation.total_discount(),
                'num_order':variation.number_order()} for variation in item.variation_set.all()[2:item.variation_set.all().count()]]
            }
            return Response(data)
        else:
            if page_no and per_page:
                page=int(page_no)
                pagesize=int(per_page)
            obj_paginator = Paginator(list_product, pagesize)
            pageitem = obj_paginator.get_page(page)
            data={'count_product':list_product.count(),
                    'pageitem':[{'item_name':item.name,'item_image':item.media_upload.all()[0].upload_file(),
                    'item_id':item.id,'item_sku':item.sku_product,'get_absolute_id':item.get_absolute_id(),
                    'count_variation':item.variation_set.all().count(),
                    'list_variation':[{'variation_id':variation.id,'color_value':variation.get_color(),
                    'size_value':variation.get_size(),'inventory':variation.inventory,
                    'discount':variation.total_discount(),
                    'num_order':variation.number_order()} for variation in item.variation_set.all()[0:3]]
                    } for item in pageitem]
                }
            return Response(data)
       
@api_view(['GET', 'POST'])
def delete_product(request):
    shop=Shop.objects.get(user=user)
    if request.method=="POST":
        item_id=request.POST.getlist('item_id')
        Item.objects.filter(id__in=item_id).delete()
        product=Item.objects.filter(shop=shop)
        page_no=request.POST.get('page_no')
        per_page=request.POST.get('per_page')
        obj_paginator = Paginator(product, per_page)
        first_page = obj_paginator.get_page(page_no)
        variation=Variation.objects.filter(item__in=first_page).order_by('-color__value')
        list_product=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),
            'id':i.id,'item_sku':i.sku_product,'get_absolute_id':i.get_absolute_id()
            } for i in first_page]
        list_variation=[{'number_order':i.number_order(),'inventory':i.inventory,'price':i.price,'sku':i.sku_classify,'color_value':i.get_color(),'size_value':i.get_size(),
        'item__id':i.item.id ,'id':i.id
                } for i in variation]
        data={
            'a':list_product,'b':list_variation,'page_range':obj_paginator.num_pages,'count_product':product.count()
        }
        return Response(data)

@api_view(['GET', 'POST'])
def voucher(request):
    token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
    access_token_obj = AccessToken(token)
    user_id=access_token_obj['user_id']
    user=User.objects.get(id=user_id)
    shop=Shop.objects.get(user=user)
    items=Item.objects.filter(shop=shop).order_by('-id')
    shipping =Shipping.objects.filter(shop=shop).last()
    vocher=Vocher.objects.filter(shop=shop)
    if vocher.exists():
        vocher=vocher.last()
    order=request.GET.get('order')
    price=request.GET.get('price')
    sort=request.GET.get('sort')
    name=request.GET.get('name')
    sku=request.GET.get('sku')
    item=request.GET.get('item')
    title=request.GET.get('title')
    q=request.GET.get('q')
    if request.method=="POST":
        item_id=request.POST.getlist('item_id')
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(item_id)])
        item_choice=Item.objects.filter(id__in=item_id).order_by(preserved)
        code_type=request.POST.get('code_type')
        name_of_the_discount_program=request.POST.get('name_of_the_discount_program')
        code = request.POST.get('code')
        valid_from=request.POST.get('valid_from')
        valid_to=request.POST.get('valid_to')
        discount_type=request.POST.get('discount_type')
        amount = request.POST.get('amount')
        percent = request.POST.get('percent')
        maximum_usage=request.POST.get('maximum_usage')
        voucher_type=request.POST.get('voucher_type')
        maximum_discount=request.POST.get('maximum_discount')
        minimum_order_value=request.POST.get('minimum_order_value')
        setting_display=request.POST.get('setting_display')
        vocher,created=Vocher.objects.get_or_create(
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
            vocher.product.add(*items)
        else:
            vocher.product.add(*item_choice)
        data={'ok':'ok' }
        return Response(data)

    else:
        if price and sort:
            if sort == "sort-asc":
                items=items.order_by('variation__price').distinct()
            else:
                items=items.order_by('-variation__price').distinct()
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif order and sort:
            if sort == "sort-asc":
                items=items.annotate(count=Count('variation__orderitem__order__id')).order_by('count')
            else:
                items=items.annotate(count=Count('variation__orderitem__order__id')).order_by('-count')
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif name and q:
            category=Category.objects.get(title=title,choice=True)
            items=items.filter(name__contains=q,category=category)
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif sku and q:
            category=Category.objects.get(title=title,choice=True)
            items=items.filter(sku_product=q,category=category)
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif item:
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        else:
            category=Category.objects.filter(item__in=items,choice=True).distinct()
            category_child=Category.objects.filter(children__in=category).exclude(parent=None).distinct()
            category_parent=Category.objects.filter(children__in=category,parent=None).distinct()
            list_category=[{'category':i.__str__()} for i in category]
            list_category_parent=[{'category':i.title} for i in category_parent]
            list_category_child=[{'category':i.__str__()} for i in category_child]
            list_item_main=[
                {'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main,'a':list_category,'b':list_category_parent,'d':list_category_child}
            return Response(data) 

@api_view(['GET', 'POST'])
def detail_voucher(request,id):
    token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
    access_token_obj = AccessToken(token)
    user_id=access_token_obj['user_id']
    user=User.objects.get(id=user_id)
    shop=Shop.objects.get(user=user)
    items=Item.objects.filter(shop=shop).order_by('-id')
    shipping =Shipping.objects.filter(shop=shop).last()
    vocher=Vocher.objects.get(id=id)
    order=request.GET.get('order')
    price=request.GET.get('price')
    sort=request.GET.get('sort')
    name=request.GET.get('name')
    sku=request.GET.get('sku')
    item=request.GET.get('item')
    title=request.GET.get('title')
    q=request.GET.get('q')
    if request.method=="POST":
        item_id=request.POST.getlist('item_id')
        item_choice=Item.objects.filter(id__in=item_id)
        vocher.code_type=request.POST.get('code_type')
        vocher.product.set([None])
        vocher.name_of_the_discount_program=request.POST.get('name_of_the_discount_program')
        vocher.code = request.POST.get('code')
        vocher.valid_from=request.POST.get('valid_from')
        vocher.valid_to=request.POST.get('valid_to')
        vocher.discount_type=request.POST.get('discount_type')
        vocher.amount = request.POST.get('amount')
        vocher.percent = request.POST.get('percent')
        vocher.maximum_usage=request.POST.get('maximum_usage')
        vocher.voucher_type=request.POST.get('voucher_type')
        vocher.maximum_discount=request.POST.get('maximum_discount')
        vocher.minimum_order_value=request.POST.get('minimum_order_value')
        vocher.setting_display=request.POST.get('setting_display')
        vocher.save()
        if vocher.code_type=="All":
            vocher.product.add(*items)
        else:
            vocher.product.add(*item_choice)
        data={'ok':'ok' }
        return Response(data)

    else:
        if price and sort:
            if sort == "sort-asc":
                items=items.order_by('variation__price').distinct()
            else:
                items=items.order_by('-variation__price').distinct()
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif order and sort:
            if sort == "sort-asc":
                items=items.annotate(count=Count('variation__orderitem__order__id')).order_by('count')
            else:
                items=items.annotate(count=Count('variation__orderitem__order__id')).order_by('-count')
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif name and q:
            category=Category.objects.get(title=title,choice=True)
            items=items.filter(name__contains=q,category=category)
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif sku and q:
            category=Category.objects.get(title=title,choice=True)
            items=items.filter(sku_product=q,category=category)
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif item:
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        else:
            data={
                'voucher':{'code_type':vocher.code_type,
                'name_of_the_discount_program':vocher.name_of_the_discount_program,
                'code':vocher.code,
                'valid_from':vocher.valid_from,
                'valid_to':vocher.valid_to,
                'discount_type':vocher.discount_type,
                'amount':vocher.amount,
                'percent':vocher.percent,
                'maximum_usage':vocher.maximum_usage,
                'voucher_type':vocher.voucher_type,
                'maximum_discount':vocher.maximum_discount,
                'minimum_order_value':vocher.minimum_order_value,
                'setting_display':vocher.setting_display},
                'items_choice':[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in vocher.product.all()]
            }
            return Response(data)
        
@api_view(['GET', 'POST'])
def shop_award(request):
    shop=Shop.objects.get(user=user)
    if request.method=="POST":
        shop_award,created=Shop_award.objects.get_or_create(
            shop=shop,
            game_name=request.POST.get("game_name"),
            from_valid=request.POST.get("valid_from"),
            to_valid=request.POST.get("valid_to"),
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

@api_view(['GET', 'POST'])
def new_combo(request):
    token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
    access_token_obj = AccessToken(token)
    user_id=access_token_obj['user_id']
    user=User.objects.get(id=user_id)
    shop=Shop.objects.get(user=user)
    promotion_combo=Promotion_combo.objects.filter(shop=shop).last()
    shipping =Shipping.objects.filter(shop=shop).last()
    items=Item.objects.filter(shop=shop).filter(Q(promotion_combo=None)| Q(promotion_combo=promotion_combo) | (Q(promotion_combo__to_valid__lt=datetime.datetime.now()) & Q(promotion_combo__isnull=False))).distinct().order_by('-id')
    order=request.GET.get('order')
    price=request.GET.get('price')
    sort=request.GET.get('sort')
    name=request.GET.get('name')
    sku=request.GET.get('sku')
    item=request.GET.get('item')
    title=request.GET.get('title')
    q=request.GET.get('q')
    if request.method=="POST":
        item_id=request.POST.getlist('item_id')
        item_id_remove=request.POST.getlist('item_id_remove')
        items=Item.objects.filter(id__in=item_id_remove)
        promotion_id=request.POST.get('promotion_id')
        page_no=request.POST.get('page_no')
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(item_id)])
        item_choice=Item.objects.filter(id__in=item_id).order_by(preserved)
        Variation.objects.filter(item__promotion_combo__to_valid__lt=datetime.datetime.now()-datetime.timedelta(seconds=10)).update(percent_discount_flash_sale=0)
        promotion_combo,created=Promotion_combo.objects.get_or_create(
            shop=shop,
            promotion_combo_name=request.POST.get('promotion_combo_name'),
            from_valid=request.POST.get('valid_from'),
            to_valid=request.POST.get('valid_to'),
            combo_type=request.POST.get('combo_type'),
            discount_percent=request.POST.get('discount_percent'),
            discount_price=request.POST.get('discount_price'),
            price_special_sale=request.POST.get('price_special_sale'),
            limit_order=request.POST.get('limit_order'),
            quantity_to_reduced=request.POST.get('quantity_to_reduced'),
            )
        promotion_combo.product.add(*item_choice)
        data={'ok':'ok'}
        return Response(data)
    else:
        if price and sort:
            if sort == "sort-asc":
                items=items.order_by('variation__price').distinct()
            else:
                items=items.order_by('-variation__price').distinct()
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif order and sort:
            if sort == "sort-asc":
                items=items.annotate(count=Count('variation__orderitem__order__id')).order_by('count')
            else:
                items=items.annotate(count=Count('variation__orderitem__order__id')).order_by('-count')
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif name and q:
            category=Category.objects.get(title=title,choice=True)
            items=items.filter(name__contains=q,category=category)
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif sku and q:
            category=Category.objects.get(title=title,choice=True)
            items=items.filter(sku_product=q,category=category)
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif item:
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
        else:
            list_item_main=[
            {'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'number_order':i.number_order(),
            'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
            'item_min':i.min_price()
            } for i in items]
            data={'c':list_item_main}
    return Response(data) 

@api_view(['GET', 'POST'])
def detail_combo(request,id):
    token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
    access_token_obj = AccessToken(token)
    user_id=access_token_obj['user_id']
    user=User.objects.get(id=user_id)
    shop=Shop.objects.get(user=user)
    promotion_combo=Promotion_combo.objects.get(id=id)
    shipping =Shipping.objects.filter(shop=shop).last()
    items=Item.objects.filter(shop=shop).filter(Q(promotion_combo=None)| Q(promotion_combo=promotion_combo) | (Q(promotion_combo__to_valid__lt=datetime.datetime.now()) & Q(promotion_combo__isnull=False))).distinct().order_by('-id')
    order=request.GET.get('order')
    price=request.GET.get('price')
    sort=request.GET.get('sort')
    name=request.GET.get('name')
    sku=request.GET.get('sku')
    item=request.GET.get('item')
    title=request.GET.get('title')
    q=request.GET.get('q')
    if request.method=="POST":
        item_id=request.POST.getlist('item_id')
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(item_id)])
        item_choice=Item.objects.filter(id__in=item_id).order_by(preserved)
        promotion.product.set([None])
        promotion_combo.promotion_combo_name=request.POST.get('promotion_combo_name')
        promotion_combo.from_valid=request.POST.get('valid_from')
        promotion_combo.to_valid=request.POST.get('valid_to')
        promotion_combo.combo_type=request.POST.get('combo_type')
        promotion_combo.discount_percent=request.POST.get('discount_percent')
        promotion_combo.discount_price=request.POST.get('discount_price')
        promotion_combo.price_special_sale=request.POST.get('price_special_sale')
        promotion_combo.limit_order=request.POST.get('limit_order')
        promotion_combo.quantity_to_reduced=request.POST.get('quantity_to_reduced')
        promotion_combo.save()
        promotion_combo.product.add(*item_choice)
        data={'ok':'ok'}
        return Response(data)
    else:
        if price and sort:
            if sort == "sort-asc":
                items=items.order_by('variation__price').distinct()
            else:
                items=items.order_by('-variation__price').distinct()
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif order and sort:
            if sort == "sort-asc":
                items=items.annotate(count=Count('variation__orderitem__order__id')).order_by('count')
            else:
                items=items.annotate(count=Count('variation__orderitem__order__id')).order_by('-count')
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif name and q:
            category=Category.objects.get(title=title,choice=True)
            items=items.filter(name__contains=q,category=category)
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif sku and q:
            category=Category.objects.get(title=title,choice=True)
            items=items.filter(sku_product=q,category=category)
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif item:
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        else:
            data={'promotion_combo':{'promotion_combo_name':promotion_combo.promotion_combo_name,
            'from_valid':promotion_combo.from_valid,
            'to_valid':promotion_combo.to_valid,
            'combo_type':promotion_combo.combo_type,
            'discount_percent':promotion_combo.discount_percent,'discount_price':promotion_combo.discount_price,
            'price_special_sale':promotion_combo.price_special_sale,'limit_order':promotion_combo.limit_order,
            'quantity_to_reduced':promotion_combo.quantity_to_reduced},
            'items_choice':[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'number_order':i.number_order(),
            'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
            'item_min':i.min_price(),'enable':True
            } for i in promotion_combo.product.all()]}
            return Response(data) 

@api_view(['GET', 'POST'])
def new_deal(request):
    token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
    access_token_obj = AccessToken(token)
    user_id=access_token_obj['user_id']
    user=User.objects.get(id=user_id)
    shop=Shop.objects.get(user=user)
    deal_expire=Buy_with_shock_deal.objects.filter(shop=shop,to_valid__lt=timezone.now())
    if request.method=="POST":
        Variation.objects.filter(item__byproduct__in=deal_expire).update(percent_discount_deal_shock=0,limited_product_bundles=0)
        deal_shock,created=Buy_with_shock_deal.objects.get_or_create(
        shop=shop,
        shock_deal_type=request.POST.get('shock_deal_type'),
        program_name_buy_with_shock_deal=request.POST.get('program_name_buy_with_shock_deal'),
        from_valid=request.POST.get('from_valid'),
        to_valid=request.POST.get('to_valid'),
        limited_product_bundles=request.POST.get('limited_product_bundles'),
        minimum_price_to_receive_gift=request.POST.get('minimum_price_to_receive_gift'),
        number_gift=request.POST.get('number_gift'),
        )
        data={
            'id':deal_shock.id
            }
        return Response(data)
    
@api_view(['GET', 'POST'])
def deal_shock(request,id):
    token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
    access_token_obj = AccessToken(token)
    user_id=access_token_obj['user_id']
    user=User.objects.get(id=user_id)
    shop=Shop.objects.get(user=user)
    shipping =Shipping.objects.filter(shop=shop).last()
    form=VocherForm()
    deal_shock=Buy_with_shock_deal.objects.get(id=id)
    items=Item.objects.filter(shop=shop).filter(Q(main_product=None) | (Q(main_product__to_valid__lt=datetime.datetime.now()) & Q(main_product__isnull=False))).distinct().order_by('-id')
    item_id=request.GET.getlist('item_id')
    item_id_off=request.GET.getlist('item_id_off')
    item_id_add=request.GET.getlist('item_id_add')
    change=request.GET.getlist('change')
    order=request.GET.get('order')
    price=request.GET.get('price')
    sort=request.GET.get('sort')
    name=request.GET.get('name')
    sku=request.GET.get('sku')
    item=request.GET.get('item')
    title=request.GET.get('title')
    variation_id=request.GET.getlist('variation_id')
    page_no = request.GET.get('page_no')
    q=request.GET.get('q')
    if request.method=="POST":
        edit=request.POST.get('edit')
        item_id=request.POST.getlist('item_id')
        byproduct_id=request.POST.getlist('byproduct_id')
        variation_id=request.POST.getlist('variation_id')
        variation_id_off=request.POST.getlist('variation_id_off')
        percent_discount=request.POST.getlist('percent_discount')
        limited_product_bundles=request.POST.getlist('limit_order')
        if edit:
            deal_shock=Buy_with_shock_deal.objects.filter(shop=shop).last()
            deal_shock.program_name_buy_with_shock_deal=request.POST.get('program_name_buy_with_shock_deal')
            deal_shock.from_valid=request.POST.get('from_valid')
            deal_shock.to_valid=request.POST.get('to_valid')
            deal_shock.limited_product_bundles=request.POST.get('limited_product_bundles')
            deal_shock.minimum_price_to_receive_gift=request.POST.get('minimum_price_to_receive_gift')
            deal_shock.number_gift=request.POST.get('number_gift')
            deal_shock.save()
            data={'shock_deal_type':deal_shock.shock_deal_type,'deal_id':deal_shock.id,'from_valid':deal_shock.from_valid,
            'to_valid':deal_shock.to_valid,'program_name_buy_with_shock_deal':deal_shock.program_name_buy_with_shock_deal,
            'limited_product_bundles':deal_shock.limited_product_bundles,
            'minimum_price_to_receive_gift':deal_shock.minimum_price_to_receive_gift,
            'number_gift':deal_shock.number_gift}
            return Response(data)
        else:
            deal_shock.main_product.set([None])
            deal_shock.byproduct.set([None])
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(byproduct_id)])
            list_byproduct=Item.objects.filter(id__in=byproduct_id).order_by(preserved)
            deal_shock.byproduct.add(*list_byproduct)
            item_main=Item.objects.filter(id__in=item_id).order_by(preserved)
            deal_shock.main_product.add(*item_main)
            variation_byproduct=Variation.objects.filter(id__in=variation_id).order_by(preserved)
            if deal_shock.shock_deal_type=='1':   
                for variation in variation_byproduct:
                    for i in range(len(percent_discount)):
                        if i==list(variation_byproduct).index(variation):
                            variation.percent_discount_deal_shock=percent_discount[i]
                            variation.limited_product_bundles=limited_product_bundles[i]
                bulk_update(variation_byproduct)
            else:
                variation_byproduct.update(percent_discount_deal_shock=100)
            Variation.objects.filter(id__in=variation_id_off).update(percent_discount_deal_shock=0)
            data={'list_byproduct':[{'item_id':item.id,'item_name':item.name,
            'item_image':item.media_upload.all()[0].upload_file(),'check':False,
            'list_variation':[{'variation_id':variation.id,'color_value':variation.get_color(),'size_value':variation.get_size(),
            'inventory':variation.inventory,'price':variation.price,
            } for variation in item.variation_set.all()
            ]} for item in list_byproduct]}
            return Response(data)
        
    else:
        if item_id and item_id_off and not q:
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(item_id)])
            items=Item.objects.filter(id__in=item_id).order_by(preserved)
            check=['On' for i in range(len(item_id))]
            check_on=['Off' for i in range(len(item_id_off))]
            for i in range(len(item_id)):
                for j in range(len(item_id_off)):
                    if item_id_off[j]==item_id[i]:
                        check[i]=check_on[j]

            list_item_main=[{'item_name':items[i].name,'item_image':items[i].media_upload.all()[0].upload_file(),'check':check[i],
                'item_id':items[i].id,'item_inventory':items[i].total_inventory(),'item_max':items[i].max_price(),
                'item_min':items[i].min_price(),'item_shipping':shipping.method,'number_order':items[i].number_order()
                } for i in range(len(items))]
           
            data={'a':list_item_main}
            return Response(data)
        elif item_id and item_id_off and q and sku:
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(item_id)])
            items=Item.objects.filter(id__in=item_id,sku_product=q).order_by(preserved)
            item_none=Item.objects.filter(shop=shop,main_product=None,byproduct=None)
            check=['On' for i in range(len(item_id))]
            check_on=['Off' for i in range(len(item_id_off))]
            for i in range(len(item_id)):
                for j in range(len(item_id_off)):
                    if item_id_off[j]==item_id[i]:
                        check[i]=check_on[j]
            list_item_main=[{'item_name':items[i].name,'item_image':items[i].media_upload.all()[0].upload_file(),'check':check[i],
                'item_id':items[i].id,'item_inventory':items[i].total_inventory(),'item_max':items[i].max_price(),
                'item_min':items[i].min_price(),'item_shipping':shipping.method,'number_order':items[i].number_order()
                } for i in range(len(items))]
           
            data={'a':list_item_main}
            return Response(data)
        elif item_id and item_id_off and q and name:
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(item_id)])
            items=Item.objects.filter(id__in=item_id,name__contains=q).order_by(preserved)
            item_none=Item.objects.filter(shop=shop,main_product=None,byproduct=None)
            check=['On' for i in range(len(item_id))]
            check_on=['Off' for i in range(len(item_id_off))]
            for i in range(len(item_id)):
                for j in range(len(item_id_off)):
                    if item_id_off[j]==item_id[i]:
                        check[i]=check_on[j]
            list_item_main=[{'item_name':items[i].name,'item_image':items[i].media_upload.all()[0].upload_file(),'check':check[i],
                'item_id':items[i].id,'item_inventory':items[i].total_inventory(),'item_max':items[i].max_price(),
                'item_min':items[i].min_price(),'item_shipping':shipping.method,'number_order':items[i].number_order()
                } for i in range(len(items))]
           
            data={'a':list_item_main}
            return Response(data)
        elif change:
            data={'valid_to':deal_shock.to_valid,'valid_from':deal_shock.from_valid,
            'name':deal_shock.program_name_buy_with_shock_deal,'shock_deal_type':deal_shock.shock_deal_type,
            'limited_product_bundles':deal_shock.limited_product_bundles,
            'minimum_price_to_receive_gift':deal_shock.minimum_price_to_receive_gift,
            'number_gift':deal_shock.number_gift
            }
            return Response(data)
        elif price and sort:
            if sort == "sort-asc":
                items=items.order_by('variation__price').distinct()
            else:
                items=items.order_by('-variation__price').distinct()
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif order and sort:
            if sort == "sort-asc":
                items=items.annotate(count=Count('variation__orderitem__order__id')).order_by('count')
            else:
                items=items.annotate(count=Count('variation__orderitem__order__id')).order_by('-count')
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif name and q and not item_id:
            category=Category.objects.get(title=title,choice=True)
            items=items.filter(name__contains=q,category=category)
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif sku and q and not item_id:
            category=Category.objects.get(title=title,choice=True)
            items=items.filter(sku_product=q,category=category)
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif item:
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif item_id and variation_id and not q:
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(item_id)])
            items=Item.objects.filter(id__in=item_id).order_by(preserved)
            obj_paginator = Paginator(items,per_page)
            preserved_variation = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(variation_id)])
            variation=Variation.objects.filter(id__in=variation_id).order_by(preserved_variation)
            first_page=obj_paginator.get_page(page_no)
            list_by_page=[{'name':first_page[i].name,'image_cover':first_page[i].media_upload.all()[0].upload_file(),'id':first_page[i].id,'item_shipping':shipping.method,
            } for i in range(len(first_page))]
            list_variation=[{'item_id':i.item.id,'price':i.price,'id':i.id,'color__value':i.get_color(),'size__value':i.get_size(),'inventory':i.inventory
            } for i in variation]
            data={'shock_deal_type':deal_shock.shock_deal_type,'a':list_by_page,'b':list_variation}
            return Response(data)
        elif item_id and variation_id and q and name:
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(item_id)])
            items=Item.objects.filter(id__in=item_id,name__contains=q).order_by(preserved)
            obj_paginator = Paginator(items,per_page)
            preserved_variation = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(variation_id)])
            variation=Variation.objects.filter(id__in=variation_id).order_by(preserved_variation)
            first_page=obj_paginator.get_page(page_no)
            list_by_page=[{'name':first_page[i].name,'image_cover':first_page[i].media_upload.all()[0].upload_file(),'id':first_page[i].id,'item_shipping':shipping.method
            } for i in range(len(first_page))]
            list_variation=[{'item_id':i.item.id,'price':i.price,'id':i.id,'color__value':i.get_color(),'size__value':i.get_size(),'inventory':i.inventory
            } for i in variation]
            data={'shock_deal_type':deal_shock.shock_deal_type,'a':list_by_page,'b':list_variation}
            return Response(data)
        elif item_id and variation_id and sku and q:
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(item_id)])
            items=Item.objects.filter(id__in=item_id,sku=q).order_by(preserved)
            obj_paginator = Paginator(items,per_page)
            preserved_variation = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(variation_id)])
            variation=Variation.objects.filter(id__in=variation_id).order_by(preserved_variation)
            first_page=obj_paginator.get_page(page_no)
            list_by_page=[{'name':first_page[i].name,'image_cover':first_page[i].media_upload.all()[0].upload_file(),'id':first_page[i].id,'item_shipping':shipping.method,
            } for i in range(len(first_page))]
            list_variation=[{'item_id':i.item.id,'price':i.price,'id':i.id,'color__value':i.get_color(),'size__value':i.get_size(),'inventory':i.inventory
            } for i in variation]
            data={'shock_deal_type':deal_shock.shock_deal_type,'a':list_by_page,'b':list_variation}
            return Response(data)
        elif item_id and not q:
            check=['On' for i in range(len(item_id))]
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(item_id)])
            items=Item.objects.filter(id__in=item_id).order_by(preserved)
            list_item_main=[{'item_name':items[i].name,'item_image':items[i].media_upload.all()[0].upload_file(),
                'item_id':items[i].id,'item_inventory':items[i].total_inventory(),'item_max':items[i].max_price(),'check':check[i],
                'item_min':items[i].min_price(),'item_shipping':shipping.method,'number_order':items[i].number_order()
            } for i in range(len(items))] 
            data={'a':list_item_main}
            return Response(data)
        elif item_id and sku and q:
            check=['On' for i in range(len(item_id))]
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(item_id)])
            items=Item.objects.filter(id__in=item_id,sku_product=q).order_by(preserved)
            list_item_main=[{'item_name':items[i].name,'item_image':items[i].media_upload.all()[0].upload_file(),
                'item_id':items[i].id,'item_inventory':items[i].total_inventory(),'item_max':items[i].max_price(),'check':check[i],
                'item_min':items[i].min_price(),'item_shipping':shipping.method,'number_order':items[i].number_order()
            } for i in range(len(items))] 
            data={'a':list_item_main}
            return Response(data)
        elif item_id and name and q:
            check=['On' for i in range(len(item_id))]
            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(item_id)])
            items=Item.objects.filter(id__in=item_id,name__contains=q).order_by(preserved)
            list_item_main=[{'item_name':items[i].name,'item_image':items[i].media_upload.all()[0].upload_file(),'check':check[i],
                'item_id':items[i].id,'item_inventory':items[i].total_inventory(),'item_max':items[i].max_price(),
                'item_min':items[i].min_price(),'item_shipping':shipping.method,'number_order':items[i].number_order()
            } for i in range(len(items))] 
            data={'a':list_item_main}
            return Response(data)
        else:
            data={'deal_shock':{'shock_deal_type':deal_shock.shock_deal_type,'deal_id':deal_shock.id,'from_valid':deal_shock.from_valid,
            'to_valid':deal_shock.to_valid,'program_name_buy_with_shock_deal':deal_shock.program_name_buy_with_shock_deal,
            'limited_product_bundles':deal_shock.limited_product_bundles,
            'minimum_price_to_receive_gift':deal_shock.minimum_price_to_receive_gift,
            'number_gift':deal_shock.number_gift},'byproduct_choice':[{'item_id':item.id,'item_name':item.name,
            'item_image':item.media_upload.all()[0].upload_file(),'check':False,
            'list_variation':[{'variation_id':variation.id,'color_value':variation.get_color(),'size_value':variation.get_size(),
            'inventory':variation.inventory,'price':variation.price,'discount_price':variation.price*(1-variation.percent_discount_deal_shock/100),'percent_discount':variation.percent_discount_deal_shock,
            'limit_order':variation.limited_product_bundles
            } for variation in item.variation_set.all()
            ]} for item in deal_shock.byproduct.all()],'items_choice':[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in deal_shock.main_product.all()]}
            return Response(data)
      
@api_view(['GET', 'POST'])
def new_program(request):
    token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
    access_token_obj = AccessToken(token)
    user_id=access_token_obj['user_id']
    user=User.objects.get(id=user_id)
    shop=Shop.objects.get(user=user)
    program_expire=Shop_program.objects.filter(shop=shop,to_valid__lt=timezone.now())
    shipping =Shipping.objects.filter(shop=shop).last()
    items=Item.objects.filter(shop=shop).filter(Q(shop_program=None) | (Q(shop_program__to_valid__lt=datetime.datetime.now()) & Q(shop_program__isnull=False))).distinct()
    order=request.GET.get('order')
    price=request.GET.get('price')
    sort=request.GET.get('sort')
    name=request.GET.get('name')
    sku=request.GET.get('sku')
    item=request.GET.get('item')
    title=request.GET.get('title')
    q=request.GET.get('q')
    if request.method=="POST": 
        name_program=request.POST.get('name_program')
        valid_from=request.POST.get('valid_from')
        valid_to=request.POST.get('valid_from')
        item_id=request.POST.getlist('item_id')
        variation_id=request.POST.getlist('variation_id')
        percent_discount=request.POST.getlist('percent_discount')
        number_of_promotional_products=request.POST.getlist('number_of_promotional_products')
        limit_order=request.POST.getlist('limit_order')
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(item_id)])
        list_products=Item.objects.filter(id__in=item_id).order_by(preserved)
        list_variation=Variation.objects.filter(id__in=variation_id)
        Variation.objects.filter(item__shop_program__in=program_expire).update(percent_discount=0)
        if item_id and not variation_id:
            data={'list_product':[{'item_id':item.id,'item_name':item.name,
            'item_image':item.media_upload.all()[0].upload_file(),'check':False,
            'list_variation':[{'variation_id':variation.id,'color_value':variation.get_color(),'size_value':variation.get_size(),
            'inventory':variation.inventory,'price':variation.price,
            } for variation in item.variation_set.all()
            ]} for item in list_products]}
            return Response(data)
        else:
            shop_program,created=Shop_program.objects.get_or_create(
                name_program=name_program,
                from_valid=valid_from,
                to_valid=valid_to,
                shop=shop,
                )
            shop_program.product.add(*list_products)
            for variation in list_variation:
                for i in range(len(percent_discount)):
                    if i==list(variation_byproduct).index(variation):
                        variation.percent_discount_deal_shock=percent_discount[i]
                        variation.number_of_promotional_products=number_of_promotional_products[i]
            bulk_update(variation_byproduct)
            for item in list_products:
                for i in range(len(limit_order)):
                    if i==list(list_products).index(item):
                        item.quantity_limit=limit_order[i]
            bulk_update(list_products,batch_size=200)
            data={'ok':'ok'}
            return Response(data)
    else:
        if price and sort:
            if sort == "sort-asc":
                items=items.order_by('variation__price').distinct()
            else:
                items=items.order_by('-variation__price').distinct()
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif order and sort:
            if sort == "sort-asc":
                items=items.filter(variation__orderitem__order__ordered=True).annotate(count=Count('variation__orderitem__order__ordered')).order_by('count')
            else:
                items=items.filter(variation__orderitem__order__ordered=True).annotate(count=Count('variation__orderitem__order__ordered')).order_by('-count')
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif name and q:
            category=Category.objects.get(title=title,choice=True)
            items=items.filter(name__contains=q,category=category)
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif sku and q:
            category=Category.objects.get(title=title,choice=True)
            items=items.filter(sku_product=q,category=category)
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif item:
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        else:
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)

@api_view(['GET', 'POST'])
def detail_program(request,id):
    token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
    access_token_obj = AccessToken(token)
    user_id=access_token_obj['user_id']
    user=User.objects.get(id=user_id)
    shop=Shop.objects.get(user=user)
    shipping =Shipping.objects.filter(shop=shop).last()
    shop_program=Shop_program.objects.get(id=id)
    items=Item.objects.filter(shop=shop).filter(Q(shop_program=None)|Q(shop_program=shop_program) | (Q(shop_program__to_valid__lt=datetime.datetime.now()) & Q(shop_program__isnull=False)))
    order=request.GET.get('order')
    price=request.GET.get('price')
    sort=request.GET.get('sort')
    name=request.GET.get('name')
    sku=request.GET.get('sku')
    item=request.GET.get('item')
    title=request.GET.get('title')
    q=request.GET.get('q')
    if request.method=="POST": 
        name_program=request.POST.get('name_program')
        valid_from=request.POST.get('valid_from')
        valid_to=request.POST.get('valid_from')
        item_id=request.POST.getlist('item_id')
        variation_id=request.POST.getlist('variation_id')
        variation_id_off=request.POST.getlist('variation_id_off')
        percent_discount=request.POST.getlist('percent_discount')
        number_of_promotional_products=request.POST.getlist('number_of_promotional_products')
        limit_order=request.POST.getlist('limit_order')
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(item_id)])
        list_products=Item.objects.filter(id__in=item_id).order_by(preserved)
        list_variation=Variation.objects.filter(id__in=variation_id)
        if item_id and not variation_id:
            data={'list_product':[{'item_id':item.id,'item_name':item.name,
            'item_image':item.media_upload.all()[0].upload_file(),'check':False,
            'list_variation':[{'variation_id':variation.id,'color_value':variation.get_color(),'size_value':variation.get_size(),
            'inventory':variation.inventory,'price':variation.price,
            } for variation in item.variation_set.all()
            ]} for item in list_product]}
            return Response(data)
        else:
            shop_program.product.set([None])
            shop_program.name_program=name_program
            shop_program.from_valid=valid_from
            shop_program.to_valid=valid_to
            shop_program.save()
            shop_program.product.add(*list_products)
            for variation in list_variation:
                for i in range(len(percent_discount)):
                    if i==list(variation_byproduct).index(variation):
                        variation.percent_discount_deal_shock=percent_discount[i]
                        variation.number_of_promotional_products=number_of_promotional_products[i]
            bulk_update(variation_byproduct)
            for item in list_products:
                for i in range(len(limit_order)):
                    if i==list(list_products).index(item):
                        item.quantity_limit=limit_order[i]
            bulk_update(list_products)
            Variation.objects.filter(id__in=variation_id_off).update(percent_discount_deal_shock=0)
            data={'ok':'ok'}
            return Response(data)
    else:
        if price and sort:
            if sort == "sort-asc":
                items=items.order_by('variation__price').distinct()
            else:
                items=items.order_by('-variation__price').distinct()
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif order and sort:
            if sort == "sort-asc":
                items=items.filter(variation__orderitem__order__ordered=True).annotate(count=Count('variation__orderitem__order__ordered')).order_by('count')
            else:
                items=items.filter(variation__orderitem__order__ordered=True).annotate(count=Count('variation__orderitem__order__ordered')).order_by('-count')
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif name and q:
            category=Category.objects.get(title=title,choice=True)
            items=items.filter(name__contains=q,category=category)
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif sku and q:
            category=Category.objects.get(title=title,choice=True)
            items=items.filter(sku_product=q,category=category)
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif item:
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        else:
            data={'program':{'from_valid':shop_program.from_valid,'name_program':shop_program.name_program,
            'to_valid':shop_program.to_valid},'list_product':[{'item_id':item.id,'item_name':item.name,
            'limit_order':item.quantity_limit,
            'item_image':item.media_upload.all()[0].upload_file(),'check':False,
            'list_variation':[{'variation_id':variation.id,'color_value':variation.get_color(),'size_value':variation.get_size(),
            'inventory':variation.inventory,'price':variation.price,'discount_price':variation.price*(1-variation.percent_discount/100),'percent_discount':variation.percent_discount,
            'number_of_promotional_products':variation.number_of_promotional_products
            } for variation in item.variation_set.all()
            ]} for item in shop_program.product.all()]}
            return Response(data)
       
@api_view(['GET', 'POST'])
def new_flashsale(request):
    token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
    access_token_obj = AccessToken(token)
    user_id=access_token_obj['user_id']
    user=User.objects.get(id=user_id)
    shop=Shop.objects.get(user=user)
    order=request.GET.get('order')
    price=request.GET.get('price')
    sort=request.GET.get('sort')
    name=request.GET.get('name')
    sku=request.GET.get('sku')
    item=request.GET.get('item')
    title=request.GET.get('title')
    shipping =Shipping.objects.filter(shop=shop).last()
    flash_sale_expire=Flash_sale.objects.filter(shop=shop,to_valid__lt=timezone.now())
    items=Item.objects.filter(shop=shop).filter(Q(flash_sale=None) | (Q(flash_sale__to_valid__lt=datetime.datetime.now()) & Q(flash_sale__isnull=False))).distinct()
    q=request.GET.get('q')
    if request.method=="POST":
        item_id=request.POST.getlist('item_id')
        variation_id=request.POST.get('variation_id')
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(item_id)])
        items=Item.objects.filter(id__in=item_id).order_by(preserved)
        if item_id and not variation_id:
            data={'list_product':[{'item_id':item.id,'item_name':item.name,
            'item_image':item.media_upload.all()[0].upload_file(),'check':False,
            'list_variation':[{'variation_id':variation.id,'color_value':variation.get_color(),'size_value':variation.get_size(),
            'inventory':variation.inventory,'price':variation.price,
            } for variation in item.variation_set.all()
            ]} for item in items]}
            return Response(data)
        else:
            Variation.objects.filter(item__flash_sale__in=flash_sale_expire).update(percent_discount_flash_sale=0,quantity_flash_sale_products=0)
            flash_sale,created=Flash_sale.objects.get_or_create(
                shop=shop,
                from_valid=request.POST.get('from_valid'),
                to_valid=request.POST.get('to_valid'),
                )
            flash_sale.product.add(*items)
            variation=Variation.objects.filter(item__in=items)
            Variation.objects.filter(item__flash_sale__to_valid__lt=datetime.datetime.now()-datetime.timedelta(seconds=10)).update(percent_discount_flash_sale=0)
            list_item=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'id':i.id
                } for i in items]
            data={'flash_sale_id':flash_sale.id ,'a':list_item,'b':list(variation.values('price','inventory','color__value','size__value','item__id','id'))}
            return Response(data)
    else:
        if price and sort:
            if sort == "sort-asc":
                items=items.order_by('variation__price').distinct()
            else:
                items=items.order_by('-variation__price').distinct()
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif order and sort:
            if sort == "sort-asc":
                items=items.annotate(count=Count('variation__orderitem__order__id')).order_by('count')
            else:
                items=items.annotate(count=Count('variation__orderitem__order__id')).order_by('-count')
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif name and q:
            category=Category.objects.get(title=title,choice=True)
            items=items.filter(name__contains=q,category=category)
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif sku and q:
            category=Category.objects.get(title=title,choice=True)
            items=items.filter(sku_product=q,category=category)
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        else:
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)

@api_view(['GET', 'POST'])
def detail_flashsale(request,id):
    token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
    access_token_obj = AccessToken(token)
    user_id=access_token_obj['user_id']
    user=User.objects.get(id=user_id)
    shop=Shop.objects.get(user=user)
    items=Item.objects.filter(shop=shop)
    order=request.GET.get('order')
    price=request.GET.get('price')
    sort=request.GET.get('sort')
    name=request.GET.get('name')
    sku=request.GET.get('sku')
    item=request.GET.get('item')
    title=request.GET.get('title')
    flash_sale=Flash_sale.objects.get(id=id)
    shipping =Shipping.objects.filter(shop=shop).last()
    items=Item.objects.filter(shop=shop).filter(Q(flash_sale=None)| Q(flash_sale=flash_sale) | (Q(flash_sale__to_valid__lt=datetime.datetime.now()) & Q(flash_sale__isnull=False))).distinct()
    q=request.GET.get('q')
    if request.method=="POST":
        item_id=request.POST.getlist('item_id')
        variation_id=request.POST.getlist('variation_id')
        percent_discount=request.POST.getlist('percent_discount')
        number_flash_sale_products=request.POST.getlist('number_flash_sale_products')
        quantity_limit_flash_sale=request.POST.getlist('limit_order')
        preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(item_id)])
        items=Item.objects.filter(id__in=item_id).order_by(preserved)
        variations=Variation.objects.filter(id__in=variation_id)
        if item_id and not variation_id:
            data={'list_product':[{'item_id':item.id,'item_name':item.name,
            'item_image':item.media_upload.all()[0].upload_file(),'check':False,
            'list_variation':[{'variation_id':variation.id,'color_value':variation.get_color(),'size_value':variation.get_size(),
            'inventory':variation.inventory,'price':variation.price,
            } for variation in item.variation_set.all()
            ]} for item in items]}
            return Response(data)
        elif variation_id and item_id:
            flash_sale.product.set([None])
            flash_sale.product.add(*items)
            for item in items:
                for i in range(len(quantity_limit_flash_sale)):
                    if i==list(items).index(item):
                        item.quantity_limit_flash_sale=quantity_limit_flash_sale[i]
            bulk_update(items)
            for variation in variations:
                for i in range(len(percent_discount)):
                    if i==list(variations).index(variation):
                        variation.percent_discount_flash_sale=percent_discount[i]
                        variation.number_of_promotional_flash_sale_products=number_flash_sale_products[i]
            bulk_update(variations)
            data={'a':'a'}
            return Response(data)
        else:
            flash_sale.from_valid=request.POST.get('from_valid')
            flash_sale.to_valid=request.POST.get('to_valid')
            flash_sale.save()
            data={'a':'a'}
            return Response(data)
    else:
        if price and sort:
            if sort == "sort-asc":
                items=items.order_by('variation__price').distinct()
            else:
                items=items.order_by('-variation__price').distinct()
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif order and sort:
            if sort == "sort-asc":
                items=items.annotate(count=Count('variation__orderitem__order__id')).order_by('count')
            else:
                items=items.annotate(count=Count('variation__orderitem__order__id')).order_by('-count')
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif name and q:
            category=Category.objects.get(title=title,choice=True)
            items=items.filter(name__contains=q,category=category)
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif sku and q:
            category=Category.objects.get(title=title,choice=True)
            items=items.filter(sku_product=q,category=category)
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        elif item:
            list_item_main=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_shipping':shipping.method,'number_order':i.number_order(),
                'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                'item_min':i.min_price()
                } for i in items]
            data={'c':list_item_main}
            return Response(data)
        else:
            data={
                'flashsale':{'from_valid':flash_sale.from_valid,'to_valid':flash_sale.to_valid},
                'list_product':[{'item_id':item.id,'item_name':item.name,
                'item_image':item.media_upload.all()[0].upload_file(),'check':False,
                'list_variation':[{'variation_id':variation.id,'color_value':variation.get_color(),'size_value':variation.get_size(),
                'inventory':variation.inventory,'price':variation.price,'discount_price':variation.price*(1-variation.percent_discount_flash_sale/100),'percent_discount':variation.percent_discount_flash_sale,
                'number_of_promotional_products':variation.quantity_flash_sale_products
                } for variation in item.variation_set.all()
                ]} for item in flash_sale.product.all()]
            }
            return Response(data)

@api_view(['GET', 'POST'])
def shipping(request):
    token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
    access_token_obj = AccessToken(token)
    user_id=access_token_obj['user_id']
    user=User.objects.get(id=user_id)
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
    token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
    access_token_obj = AccessToken(token)
    user_id=access_token_obj['user_id']
    user=User.objects.get(id=user_id)
    shop=Shop.objects.get(user=user)
    shipping_shop=shop.shipping.all()
    data={'shipping_shop':[{'id':i.id,'method':i.method,'unit':i.shipping_unit} for i in shipping_shop]}
    return Response(data)

@api_view(['GET', 'POST'])
def update_image(request):
    token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
    access_token_obj = AccessToken(token)
    user_id=access_token_obj['user_id']
    user=User.objects.get(id=user_id)
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
               'file':uploaditem.upload_file()
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
                'id':uploaditem.id,'file':uploaditem.upload_file(),'file_preview':uploaditem.file_preview(),
                'duration':uploaditem.duration
            }
            return Response(data)

@api_view(['GET', 'POST'])
def add_item(request):
    token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
    if request.method=='POST':
        access_token_obj = AccessToken(token)
        user_id=access_token_obj['user_id']
        user=User.objects.get(id=user_id)
        shop=Shop.objects.get(user=user)
        #item
        category_id=request.POST.get('category_id')
        from_quantity=request.POST.getlist('from_quantity')
        to_quantity=request.POST.getlist('to_quantity')
        price_range=request.POST.getlist('price_range')
        category= Category.objects.get(id=category_id)
        
        buy_more=Buy_more_discount.objects.bulk_create([
            Buy_more_discount(
               from_quantity=from_quantity[i],
               to_quantity=to_quantity[i],
               price=price_range[i],
            )
            for i in range(len(from_quantity))
        ])
        
        name=request.POST.get('name')
        description = request.POST.get('description')
        item = Item.objects.create(shop = shop,name = name,category=category,description=description)
        item.slug=name + '.' + str(item.id)
        file_id=request.POST.getlist('file_id')
        file_id_remove=request.POST.getlist('file_id_remove')
        item.brand= request.POST.get('brand')
        item.weight=request.POST.get('weight')
        item.height=request.POST.get('height')
        item.length=request.POST.get('length')
        item.width=request.POST.get('width')
        item.save()
        if len(from_quantity)>0:
            list_buy_more=Buy_more_discount.objects.all().order_by('-id')[:len(from_quantity)]
            item.buy_more_discount.add(*list_buy_more)
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
    item=Item.objects.get(id=id)
    token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
    access_token_obj = AccessToken(token)
    user_id=access_token_obj['user_id']
    user=User.objects.get(id=user_id)
    shop=Shop.objects.get(user=user)
    
    if request.method=="POST":
        #item
        from_quantity=request.POST.getlist('from_quantity')
        to_quantity=request.POST.getlist('to_quantity')
        price_range=request.POST.getlist('price_range')
        category= Category.objects.get(id=category_id)
        
        buy_more=Buy_more_discount.objects.bulk_create([
            Buy_more_discount(
               from_quantity=from_quantity[i],
               to_quantity=to_quantity[i],
               price=price_range[i],
            )
            for i in range(len(from_quantity))
            ])
        
        name=request.POST.get('name')
        category_id=request.POST.get('category_id')
        description = request.POST.get('description')
        item = Item.objects.create(shop = shop,name = name,category=category,description=description,slug=name)
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
        Buy_more_discount.objects.filter(item=item).delete()
       
        buy_more=Buy_more_discount.objects.bulk_create([
            Buy_more_discount(
               from_quantity=from_quantity[i],
               to_quantity=to_quantity[i],
               price=price_range[i],
            )
            for i in range(len(from_quantity))
            ])
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
        list_color=Color.objects.filter(variation__item=item).distinct()
        detail_item=Detail_Item.objects.filter(item=item).values()
        buymore=item.buy_more_discount.all()
        variations=Variation.objects.filter(item=item,size=None)
        list_variation=[{'value':color.value,'price':'','sku':'','inventory':'',
        'list_variation':[{'value':variation.size.value,'price':variation.price,
        'inventory':variation.inventory,'sku':variation.sku_classify} for variation in color.variation_set.all()]} for color in list_color]
        if variations.exists():
            list_variation=[{'value':variation.color.value,'price':variation.price,'sku':variation.sku_classify,'inventory':variation.inventory,
            'list_variation':[]} for variation in variations]
        shipping_shop=shop.shipping.all()
        shipping_item=item.shipping_choice.all()
        list_category_choice=item.category.get_ancestors(include_self=True)
        list_category=Category.objects.all()
        data={
        'buymore':buymore.values(),
        'item_info':{'name':item.name,'id':item.id, 'height':item.height,'length':item.length,'weight':item.weight,
        'description':item.description,'status':item.status,'sku_product':item.sku_product},
        'list_category_choice':[{'title':category.title,'id':category.id,'level':category.level,'choice':category.choice,
        'parent':category.getparent()} for category in list_category_choice],
        'list_category':[{'title':category.title,'id':category.id,'level':category.level,'choice':category.choice,
        'parent':category.getparent()} for category in list_category],
        'list_shipping_item':[{'method':shipping.method} for shipping in shipping_item],
        'shipping_shop':shipping_shop.values(),
        'media_upload':[{'file':i.upload_file(),'file_preview':i.file_preview(),
        'duration':i.duration,'filetype':i.media_type(),'id':i.id
        } for i in item.media_upload.all()],'list_size':item.get_size(),'list_color':item.get_list_color(),
        'item_detail':detail_item,'list_variation':list_variation}
        return Response(data)
@api_view(['GET', 'POST'])
def create_shop(request):
    if request.method == "POST":
        try:
            shop=Shop.objects.get(user=user)
            form=ShopForm(request.POST,request.FILES,instance=shop)
            form.save()
            messages.info(request,'ok')
            return redirect('/')
        except Exception:
            form=ShopForm(request.POST)
            if form.is_valid():
                form.save()
                usr = random.randint(1, 99999999)
                shop=Shop.objects.create(
                user=user,
                name=form.cleaned_data.get('name'),
                description = form.cleaned_data.get('description'),
                address=form.cleaned_data.get('address'),
                city=form.cleaned_data.get('city'),
                logo = form.cleaned_data.get('logo'),
                slug=re.sub('[,./\ ]', "-",name) + str(usr)
                )
                
                messages.success(request,'ok')
                return redirect('/')
            else:
                return redirect('/')
    
import calendar
import pandas as pd
@api_view(['GET', 'POST'])
def my_dashboard(request):
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token_obj = AccessToken(token)
        user_id=access_token_obj['user_id']
        user=User.objects.get(id=user_id)
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
        accepted=False
        ordered=True
        if accept:
            accepted=True
        received=[False, True]
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
                total_order_day=Order.objects.filter(shop=shop,ordered_date__date__gte=current_date,ordered=ordered,accepted=accepted,canceled=canceled,received__in=received).annotate(day=TruncHour('ordered_date')).values('day').annotate(count=Count('id')).values('day','count')
                total_amount_day=Order.objects.filter(shop=shop,ordered_date__date__gte=current_date,ordered=ordered,accepted=accepted,canceled=canceled,received__in=received).annotate(day=TruncHour('ordered_date')).values('day').annotate(sum=Sum('amount')).values('day','sum')
                result =Order.objects.filter(shop=shop,ordered=ordered,accepted=accepted,canceled=canceled,received__in=received).aggregate(
                    order=Count('id', filter=Q(ordered_date__date=current_date)),
                    order_last=Count('id', filter=Q(ordered_date__date=(current_date - timedelta(days=1)))),
                    amount=Coalesce(Sum('amount', filter=Q(ordered_date__date=current_date),output_field=FloatField()),0.0),
                    amount_last=Coalesce(Sum('amount', filter=Q(ordered_date__date=(current_date - timedelta(days=1)))),0.0),
                )

                if time=='yesterday':
                    otal_order_day=Order.objects.filter(shop=shop,ordered_date__date=yesterday,ordered=ordered,accepted=accepted,canceled=canceled,received__in=received).annotate(day=TruncHour('ordered_date')).values('day').annotate(count=Count('id')).values('day','count')
                    total_amount_day=Order.objects.filter(shop=shop,ordered_date__date=yesterday,ordered=ordered,accepted=accepted,canceled=canceled,received__in=received).annotate(day=TruncHour('ordered_date')).values('day').annotate(sum=Sum('amount')).values('day','sum')
                    result =Order.objects.filter(shop=shop,ordered=ordered,accepted=accepted,canceled=canceled,received__in=received).aggregate(
                    order=Count('id', filter=Q(ordered_date__date=yesterday)),
                    order_last=Count('id', filter=Q(ordered_date__date=(yesterday - timedelta(days=1)))),
                    amount=Coalesce(Sum('amount', filter=Q(ordered_date__date=yesterday)),0.0),
                    amount_last=Coalesce(Sum('amount', filter=Q(ordered_date__date=(yesterday - timedelta(days=1)))),0.0),
                    )
                    sum_hour=[0 for i in range(24)]
                    count_hour=[0 for i in range(24)]
                    
                elif time=='day':
                    day=pd.to_datetime(time_choice)
                    total_order=Order.objects.filter(shop=shop,ordered_date__date=day,ordered=ordered,accepted=accepted,canceled=canceled,received__in=received).annotate(day=TruncHour('ordered_date')).values('day').annotate(count=Count('id')).values('day','count')
                    total_amount=Order.objects.filter(shop=shop,ordered_date__date=day,ordered=ordered,accepted=accepted,canceled=canceled,received__in=received).annotate(day=TruncHour('ordered_date')).values('day').annotate(sum=Sum('amount')).values('day','sum')
                    result =Order.objects.filter(shop=shop,ordered=ordered,accepted=accepted,canceled=canceled,received__in=received).aggregate(
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
                total_order=Order.objects.filter(shop=shop,ordered_date__date__gte=week,ordered_date__date__lte=start_date,ordered=ordered,accepted=accepted,canceled=canceled,received__in=received).annotate(day=TruncDay('ordered_date')).values('day').annotate(count=Count('id')).values('day','count')
                total_amount=Order.objects.filter(shop=shop,ordered_date__date__gte=week,ordered_date__date__lte=start_date,ordered=ordered,accepted=accepted,canceled=canceled,received__in=received).annotate(day=TruncDay('ordered_date')).values('day').annotate(sum=Sum('amount')).values('day','sum')
                result =Order.objects.filter(shop=shop,ordered=ordered,accepted=accepted,canceled=canceled,received__in=received).aggregate(
                    order=Count('id', filter=Q(ordered_date__date__gt=week)),
                    order_last=Count('id', filter=(Q(ordered_date__date__lt=week)&Q(ordered_date__date__gte=(week - timedelta(days=7))))),
                    amount=Coalesce(Sum('amount', filter=Q(ordered_date__date__gte=week)),0.0),
                    amount_last=Coalesce(Sum('amount', filter=(Q(ordered_date__date__lt=week)&Q(ordered_date__date__gte=(week - timedelta(days=7))))),0.0),
                    )
                if time=='week':
                    week=pd.to_datetime(time_choice)
                    total_order=Order.objects.filter(shop=shop,ordered_date__week=week.isocalendar()[1],ordered_date__year=week.year,ordered=ordered,accepted=accepted,canceled=canceled,received__in=received).annotate(day=TruncDay('ordered_date')).values('day').annotate(count=Count('id')).values('day','count')
                    total_amount=Order.objects.filter(shop=shop,ordered_date__week=week.isocalendar()[1],ordered_date__year=week.year,ordered=ordered,accepted=accepted,canceled=canceled,received__in=received).annotate(day=TruncDay('ordered_date')).values('day').annotate(sum=Sum('amount')).values('day','sum')
                    result =Order.objects.filter(shop=shop,ordered=ordered,accepted=accepted,canceled=canceled,received__in=received).aggregate(
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
                total_order=Order.objects.filter(shop=shop,ordered_date__date__gte=month,ordered_date__date__lte=start_date,ordered=ordered,accepted=accepted,canceled=canceled,received__in=received).annotate(day=TruncDay('ordered_date')).values('day').annotate(count=Count('id')).values('day','count')
                total_amount=Order.objects.filter(shop=shop,ordered_date__date__gte=month,ordered_date__date__lte=start_date,ordered=ordered,accepted=accepted,canceled=canceled,received__in=received).annotate(day=TruncDay('ordered_date')).values('day').annotate(sum=Sum('amount')).values('day','sum')
                result =Order.objects.filter(shop=shop,ordered=ordered,accepted=accepted,canceled=canceled,received__in=received).aggregate(
                    order=Count('id', filter=Q(ordered_date__date__gt=month)),
                    order_last=Count('id', filter=(Q(ordered_date__date__lt=month)&Q(ordered_date__date__gte=(month - timedelta(days=30))))),
                    amount=Coalesce(Sum('amount', filter=Q(ordered_date__date__gt=month)),0.0),
                    amount_last=Coalesce(Sum('amount', filter=(Q(ordered_date__date__lt=month)&Q(ordered_date__date__gte=(month - timedelta(days=30))))),0.0),
                ) 
                if time=='month':
                    month=pd.to_datetime(time_choice)
                    total_order=Order.objects.filter(shop=shop,ordered_date__month=month.month,ordered_date__year=month.year,ordered=ordered,accepted=accepted,canceled=canceled,received__in=received).annotate(day=TruncDay('ordered_date')).values('day').annotate(count=Count('id')).values('day','count')
                    total_amount=Order.objects.filter(shop=shop,ordered_date__month=month.month,ordered_date__year=month.year,ordered=ordered,accepted=accepted,canceled=canceled,received__in=received).annotate(day=TruncDay('ordered_date')).values('day').annotate(sum=Sum('amount')).values('day','sum')
                    result =Order.objects.filter(shop=shop,ordered=ordered,accepted=accepted,canceled=canceled,received__in=received,ordered_date__year=month.year).aggregate(
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
                result =Order.objects.filter(shop=shop,ordered_date__year=year.year,ordered=ordered,accepted=accepted,canceled=canceled,received__in=received).aggregate(
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




   


