
# Create your views here.
from django.db.models import Q
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from rest_framework.generics import (
    ListAPIView, RetrieveAPIView, CreateAPIView,
    UpdateAPIView, DestroyAPIView
)
from rest_framework_simplejwt.tokens import RefreshToken
from drf_multiple_model.views import ObjectMultipleModelAPIView
from django.core.paginator import Paginator
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from rest_framework.renderers import TemplateHTMLRenderer
from django.contrib.auth.decorators import login_required
from django.db.models import Max, Min, Count, Avg,Sum
from shop.models import *
from category.models import *
from checkout.models import *
from cart.models import *
from discount.models import *
from chat.models import *
from city.models import *
from myweb.models import *
from itemdetail.models import *
from actionorder.models import *
from rest_framework.decorators import api_view
from bulk_update.helper import bulk_update
from .serializers import ChangePasswordSerializer,UserSerializer
from rest_framework_simplejwt.tokens import AccessToken
import random
import string
import json
import datetime,jwt
from django.contrib.auth import authenticate,login,logout
from rest_framework import status,viewsets,generics
from django.contrib.auth.models import User

import paypalrestsdk
from paypalrestsdk import Sale
paypalrestsdk.configure({
  'mode': 'sandbox', #sandbox or live
  'client_id': 'AY2deOMPkfo32qrQ_fKeXYeJkJlAGPh5N-9pdDFXISyUydAwgRKRPRGhiQF6aBnG68V6czG5JsulM2mX',
  'client_secret': 'EJBIHj3VRi77Xq3DXsQCxyo0qPN7UFB2RHQZ3DOXLmvgNf1fXWC5YkKTmUrIjH-jaKMSYBrH4-9RjiHA' })

def create_ref_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=14))
class UserIDView(APIView):
    def get(self, request, *args, **kwargs):
        return Response({'userID': user.id}, status=HTTP_200_OK)

class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class LoginView(APIView):
    def post(self, request):
        username = request.data['username']
        password = request.data['password']
        user = User.objects.filter(username=username).first()
        if user is None:
            raise AuthenticationFailed('User not found!')

        if not user.check_password(password):
            raise AuthenticationFailed('Incorrect password!')

        refresh = RefreshToken.for_user(user)
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        return response(data)


class LogoutView(APIView):
    def post(self, request):
        response = Response()
        response.delete_cookie('jwt')
        response.data = {
            'message': 'success'
        }
        return response
class HomeAPIView(APIView):
    def get(self,request):
        list_flashsale=Flash_sale.objects.filter(valid_to__gt=timezone.now(),valid_from__lt=timezone.now())
        list_items=Item.objects.filter(flash_sale__in=list_flashsale).distinct()
       
        data={
            'a':[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'number_order':i.number_order(),
            'percent_discount':i.discount_flash_sale(),'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),'item_url':i.get_absolute_url(),
            'item_min':i.min_price(),'quantity_limit_flash_sale':i.quantity_limit_flash_sale} for i in list_items],
            'list_flashsale':list_flashsale.values('valid_from','valid_to')
        }
        return Response(data)

class CategoryListView(APIView):
    permission_classes = (AllowAny,)
    def get(self,request):
        category_parent=Category.objects.all().order_by('id')
        list_category_parent=[{'title':i.title,'image':i.image.url,'url':i.get_absolute_url()} for i in category_parent if i.image]
        data={'b':list_category_parent,'ik':'fkkk'}
        
        return Response(data)

class DetailAPIView(APIView):
    def get(self, request,slug):
        category=Category.objects.filter(slug=slug)
        item=Item.objects.filter(slug=slug)
        shop=Shop.objects.filter(slug=slug)
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        page_no=1
        page = request.GET.get('page')
        sort_price=request.GET.get('price_sort')
        minprice=request.GET.get('minPrice')
        maxprice=request.GET.get('maxPrice')
        rating_score=request.GET.get('rating')
        order=request.GET.get('order')
        sortby=request.GET.get('sortby')
        brand=request.GET.get('brand')
        status=request.GET.get('status')
        locations=request.GET.get('locations')
        unitdelivery=request.GET.get('unitdelivery')
        shoptype=request.GET.get('shoptype')
        categoryID=request.GET.get('categoryID')
        if category.exists():
            category=Category.objects.get(slug=slug)
            category_children=Category.objects.filter(parent=category)
            category_choice=category.get_descendants(include_self=False).filter(choice=True)
            list_items=Item.objects.filter(category__in=category_choice)
            items=Item.objects.filter(category__in=category_choice)
            list_shop=Shop.objects.filter(item__in=list_items)
            if categoryID:
                items=items.filter(category__id=categoryID)
            if brand:
                items=items.filter(brand=brand)
            if status:
                items=items.filter(status=status)
            if locations:
                items=items.filter(shop__city=locations)
            if shoptype:
                items=items.filter(shop_type=shoptype)
            if rating_score:
                rating=int(rating_score)
                items=items.annotate(avg_rating= Avg('variation__orderitem__review__review_rating')).filter(avg_rating__gte=rating)
            if maxprice and minprice:
                max_price=int(maxprice)
                min_price=int(minprice)
                items=items.annotate(min=Min('variation__price')).filter(min__gte=min_price,min__lte=max_price)
            if sortby:
                items=items.filter(variation__orderitem__order__ordered=True)
                if sortby=='pop':
                    items=items.annotate(count_like= Count('liked')).annotate(count_order= Count('variation__orderitem__order')).annotate(count_order= Count('variation__orderitem__order')).annotate(count_review= Count('variation__orderitem__review')).order_by('-count_like','-count_review','-count_order')
                elif sortby=='ctime':
                    items=items.annotate(count_order= Count('variation__orderitem__order__id')).annotate(count_review= Count('variation__orderitem__review')).order_by('-id')
                elif sort_by=='price':
                    items=items.annotate(avg_price= Avg('variation__price')).order_by('avg_price')
                    if order=='desc':
                        items=items.annotate(avg_price= Avg('variation__price')).order_by('-avg_price')
            paginator = Paginator(items,30)
            page_obj = paginator.get_page(page)
            shoptype=[{'value':shop.shop_type,'name':shop.get_shop_type_display()} for shop in list_shop]
            status=[{'value':item.status,'name':item.get_status_display()} for item in list_items]
            data={
                'image_home':[{'image':i.image.url,'url':i.url_field} for i in category.image_category.all()],
                'shoptype':list({item['value']:item for item in shoptype}.values()),
                'cities':list(set([shop.city for shop in list_shop])),
                'unitdelivery':list(set(['Nhanh','Hỏa tốc'])),
                'brands':list(set([item.brand for item in list_items])),
                'status':list({item['value']:item for item in status}.values()),
                'category_choice':[{'id':i.id,'title':i.title,'count_item':i.item_set.all().count(),'url':i.get_absolute_url()} for i in category_choice],
                'category_info':{'title':category.title,'image':category.image.url,'id':category.id},
                'category_children':[{'id':i.id,'title':i.title,'url':i.get_absolute_url()} for i in category_children],
                'list_item_page':[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),
                'item_url':i.get_absolute_url(),'percent_discount':i.percent_discount(),'item_min':i.min_price(),
                'shop_city':i.shop.city,'item_brand':i.brand,'voucher':i.get_voucher(),
                'item_review':i.average_review(),'num_like':i.num_like(),'item_max':i.max_price(),
                'program_valid':i.count_program_valid(),'promotion':i.get_promotion(),
                'shock_deal':i.shock_deal_type(),'num_order':i.number_order()
                }
            for i in page_obj],'page_count':paginator.num_pages
            }
            return Response(data)

        elif item.exists():
            item=Item.objects.get(slug=slug)
            items=Item.objects.filter(shop=item.shop)
            vouchers=Vocher.objects.filter(product=item,valid_to__gte=datetime.datetime.now()-datetime.timedelta(seconds=10))
            deal_shock=Buy_with_shock_deal.objects.filter(main_product=item,valid_to__gt=datetime.datetime.now()-datetime.timedelta(seconds=10))
            promotion_combo=Promotion_combo.objects.filter(product=item,valid_to__gt=datetime.datetime.now()-datetime.timedelta(seconds=10))
            flash_sale=Flash_sale.objects.filter(product=item,valid_to__gt=datetime.datetime.now()-datetime.timedelta(seconds=10))
            order=Order.objects.filter(items__product__item=item,received=True)
            reviews=ReView.objects.filter(orderitem__product__item=item).distinct()
            variation=Variation.objects.filter(item=item).distinct()
            item_detail=Detail_Item.objects.filter(item=item).values()

            data={'count_variation':item.count_variation(),
            'item_name':item.name,'min_price':item.min_price(),'max_price':item.max_price(),
            'id':item.id,'num_like':item.num_like(),'percent_discount':item.percent_discount(),
            'item_review':item.average_review(),'count_review':item.count_review(),
            'category':item.category.get_full_category(),'media_upload':[{'file':i.upload_file(),
            'image_preview':i.file_preview(),'duration':i.duration,'media_type':i.media_type(),
            } for i in item.media_upload.all()],'size':item.get_size(),'color':item.get_color(),
            'item_inventory':item.total_inventory(),
            'num_order':item.number_order(),'description':item.description,
            'program_valid':item.count_program_valid(),
            'shock_deal_type':item.shock_deal_type(),'item_detail':item_detail,
            'deal_shock':list(deal_shock.values()),'flash_sale':list(flash_sale.values()),
            'promotion_combo':list(promotion_combo.values()),'shop_user':item.shop.user.id,
            'voucher':list(vouchers.values()),
            'reviews':[{'id':review.id,'review_text':review.review_text,'created':review.created,
                'info_more':review.info_more,'rating_anonymous':review.anonymous_review,
                'rating_product':review.rating_product,'rating_seller_service':review.rating_seller_service,
                'rating_shipping_service':review.rating_shipping_service,'review_rating':review.review_rating,
                'edited':review.edited,'list_file':[{'filetype':file.filetype(),'file':file.upload_file(),
                'media_preview':file.media_preview(),'duration':file.duration,'file_id':file.id}
                for file in review.media_upload.all()],
                'item_url':review.orderitem.product.item.get_absolute_url(),
                'item_name':review.orderitem.product.item.name,'color_value':review.orderitem.product.get_color(),
                'size_value':review.orderitem.product.get_size(),'user':review.user.username,'shop':review.shop_name(),
                'url_shop':review.user.shop.get_absolute_url()
                } for review in reviews] 
            }
            
            if token:
                if not jwt.ExpiredSignatureError:
                    access_token_obj = AccessToken(token)
                    user_id=access_token_obj['user_id']
                    user=User.objects.get(id=user_id)
                    like=False
                    if user in item.liked.all():
                        like=True
                    threads = Thread.objects.filter(participants=user).order_by('timestamp')
                    data.update({'user':user_id,'like':like,'voucher_user':[True if user in voucher.user.all() else False for voucher in vouchers],
                    'list_threads':[{'id':thread.id,'count_message':thread.count_message(),'list_participants':[user.id for user in thread.participants.all() ]} for thread in threads]})
            return Response(data)
        elif shop.exists():
            shop=Shop.objects.get(slug=slug)
            list_voucher=Vocher.objects.filter(shop=shop,valid_to__gt=timezone.now(),valid_from__lte=timezone.now())
            deal_shock=Buy_with_shock_deal.objects.filter(shop=shop,valid_to__gt=timezone.now(),valid_from__lte=timezone.now())
            main_product=Item.objects.filter(main_product__in=deal_shock)
            promotion_combo=Promotion_combo.objects.filter(shop=shop,valid_to__gt=timezone.now(),valid_from__lte=timezone.now())
            item_combo=Item.objects.filter(promotion_combo__in=promotion_combo)
            items=Item.objects.filter(shop=shop)
            category_children=Category.objects.filter(item__shop=shop).distinct()
            if categoryID:
                category_choice=Category.objects.get(id=categoryID)
                items=items.filter(category=category_choice)
            if rating_score:
                rating=int(rating_score)
                items=items.annotate(avg_rating= Avg('variation__orderitem__review__review_rating')).filter(avg_rating__gte=rating)
            if maxprice and minprice:
                max_price=int(maxprice)
                min_price=int(minprice)
                items=items.annotate(min=Min('variation__price')).filter(min__gte=min_price,min__lte=max_price)
            if sortby:
                items=items.filter(variation__orderitem__order__ordered=True)
                if sortby=='pop':
                    items=items.annotate(count_like= Count('liked')).annotate(count_order= Count('variation__orderitem__order')).annotate(count_order= Count('variation__orderitem__order')).annotate(count_review= Count('variation__orderitem__review')).order_by('-count_like','-count_review','-count_order')
                elif sortby=='ctime':
                    items=items.annotate(count_order= Count('variation__orderitem__order__id')).annotate(count_review= Count('variation__orderitem__review')).order_by('-id')
                elif sort_by=='price':
                    items=items.annotate(avg_price= Avg('variation__price')).order_by('avg_price')
                    if order=='desc':
                        items=items.annotate(avg_price= Avg('variation__price')).order_by('-avg_price')
            paginator = Paginator(items,30)
            page_obj = paginator.get_page(page)
            count_follow=Shop.objects.filter(followers=shop.user).count()
            data={'shop_logo':shop.logo.url,'shop_url':shop.get_absolute_url(),'count_followings': count_follow,
                'shop_name':shop.name,'shop':'shop','shop_user':shop.user.id,'created':shop.create_at,
                'online':shop.user.shop.online,'num_followers':shop.num_follow(),'slug':shop.slug,
                'is_online':shop.user.shop.is_online,'count_product':shop.count_product(),
                'total_review':shop.total_review(),'averge_review':shop.averge_review(),
                'promotion_combo':[{'combo_type':promotion.combo_type,
                'quantity_to_reduced':promotion.quantity_to_reduced,'limit_order':promotion.quantity_to_reduced,
                'discount_percent':promotion.discount_percent,'discount_price':promotion.discount_price,
                'price_special_sale':promotion.price_special_sale} for promotion in promotion_combo],
                'item_combo':[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),
                'item_url':i.get_absolute_url(),'percent_discount':i.percent_discount(),'item_min':i.min_price(),
                'shop_city':i.shop.city,'item_brand':i.brand,'voucher':i.get_voucher(),
                'item_review':i.average_review(),'num_like':i.num_like(),'item_max':i.max_price()} for i in item_combo],
                'list_item_page':[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),
                'item_url':i.get_absolute_url(),'percent_discount':i.percent_discount(),'item_min':i.min_price(),
                'shop_city':i.shop.city,'item_brand':i.brand,'voucher':i.get_voucher(),
                'item_review':i.average_review(),'num_like':i.num_like(),'item_max':i.max_price(),
                'program_valid':i.count_program_valid(),'promotion':i.get_promotion(),
                'shock_deal':i.shock_deal_type(),'num_order':i.number_order()
                }
                for i in page_obj],'page_count':paginator.num_pages,'list_voucher':list_voucher.values(),
                'main_product':[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),
                'item_url':i.get_absolute_url(),'percent_discount':i.percent_discount(),'item_min':i.min_price(),
                'shop_city':i.shop.city,'item_brand':i.brand,'voucher':i.get_voucher(),
                'item_review':i.average_review(),'num_like':i.num_like(),'item_max':i.max_price()} for i in main_product],
                'total_order':shop.total_order(),'list_category_child':[{'title':category.title,'id':category.id,'url':category.get_absolute_url()} for category in category_children]}
            if token:
                if not jwt.ExpiredSignatureError:
                    access_token_obj = AccessToken(token,verify=True)
                    user_id=access_token_obj['user_id']
                    user=User.objects.get(id=user_id)
                    follow=False
                    if user in shop.followers.all():
                        follow=True
                    threads = Thread.objects.filter(participants=user).order_by('timestamp')
                    data.update({'user':user_id,'follow':follow,
                    'list_threads':[{'id':thread.id,'count_message':thread.count_message(),'list_participants':[user.id for user in thread.participants.all() ]} for thread in threads]})
            return Response(data)
    def post(self, request, *args, **kwargs):
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        shop_name=request.POST.get('shop_name')
        shop=Shop.objects.get(name=shop_name)
        access_token_obj = AccessToken(token)
        user_id=access_token_obj['user_id']
        user=User.objects.get(id=user_id)
        follow=False
        count_follow=Shop.objects.filter(followers=shop.user).count()
        if user in shop.followers.all():
            follow=False
            shop.followers.remove(user)
        else:
            follow=True
            shop.followers.add(user)
        data={'num_followers':shop.num_follow(),'follow':follow,'online':shop.user.shop.online,
        'num_followers':shop.num_follow(),'count_followings': count_follow,
        'is_online':shop.user.shop.is_online,'count_product':shop.count_product(),
        'total_review':shop.total_review(),'averge_review':shop.averge_review()}
        return Response(data)

class SearchitemAPIView(APIView):
    def get(self, request):
        keyword=request.GET.get('keyword')
        page = request.GET.get('page')
        minprice=request.GET.get('minPrice')
        maxprice=request.GET.get('maxPrice')
        rating_score=request.GET.get('rating')
        order=request.GET.get('order')
        sortby=request.GET.get('sortby')
        brand=request.GET.get('brand')
        status=request.GET.get('status')
        locations=request.GET.get('locations')
        unitdelivery=request.GET.get('unitdelivery')
        shoptype=request.GET.get('shoptype')
        categoryID=request.GET.get('categoryID')
        category=request.GET.get('category')
        shop=request.GET.get('shop')
        if keyword:
            list_items = Item.objects.filter(Q(name__icontains=keyword) | Q(
            name__in=keyword))
            items = Item.objects.filter(Q(name__icontains=keyword) | Q(
            name__in=keyword))
            category_choice=Category.objects.filter(item__in=list_items).distinct()
            list_shop=Shop.objects.filter(item__in=list_items)
        if shop:
            list_items=list_items.filter(shop__name=shop)
            items=items.filter(shop__name=shop).distinct()
        if categoryID:
            categoryID=int(categoryID)
            items=items.filter(category__id=categoryID)
        if category:
            category=int(category)
            category_parent=Category.objects.get(id=category)
            categories=category_parent.get_descendants(include_self=False).filter(choice=True)
            list_items=list_items.filter(category__in=categories).distinct()
            items=items.filter(category__in=categories).distinct()
        if brand:
            items=items.filter(brand=brand)
        if status:
            items=items.filter(status=status)
        if locations:
            items=items.filter(shop__city=locations)
        if shoptype:
            items=items.filter(shop_type=shoptype)
        if rating_score:
            rating=int(rating_score)
            items=items.annotate(avg_rating= Avg('variation__orderitem__review__review_rating')).filter(avg_rating__gte=rating)
        if sortby:
            if sortby=='pop':
                items=items.annotate(count_like= Count('liked')).annotate(count_order= Count('variation__orderitem__order')).annotate(count_order= Count('variation__orderitem__order')).annotate(count_review= Count('variation__orderitem__review')).order_by('-count_like','-count_review','-count_order')
            elif sortby=='ctime':
                items=items.annotate(count_order= Count('variation__orderitem__order__id')).annotate(count_review= Count('variation__orderitem__review')).order_by('-id')
            elif sortby=='price':
                items=items.annotate(avg_price= Avg('variation__price')).order_by('avg_price')
                if order=='desc':
                    items=items.annotate(avg_price= Avg('variation__price')).order_by('-avg_price')
        paginator = Paginator(items,30)
        page_obj = paginator.get_page(page)
        shoptype=[{'value':shop.shop_type,'name':shop.get_shop_type_display()} for shop in list_shop]
        status=[{'value':item.status,'name':item.get_status_display()} for item in list_items]
        data={
            'shoptype':list({item['value']:item for item in shoptype}.values()),
            'cities':list(set([shop.city for shop in list_shop])),
            'unitdelivery':list(set(['Nhanh','Hỏa tốc'])),
            'brands':list(set([item.brand for item in list_items])),
            'status':list({item['value']:item for item in status}.values()),
            'category_choice':[{'id':i.id,'title':i.title,'count_item':i.item_set.all().count(),'url':i.get_absolute_url()} for i in category_choice],
            'list_item_page':[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),
            'item_url':i.get_absolute_url(),'percent_discount':i.percent_discount(),'item_min':i.min_price(),
            'shop_city':i.shop.city,'item_brand':i.brand,'voucher':i.get_voucher(),
            'item_review':i.average_review(),'num_like':i.num_like(),'item_max':i.max_price(),
            'program_valid':i.count_program_valid(),'promotion':i.get_promotion(),
            'shock_deal':i.shock_deal_type(),'num_order':i.number_order()
            }
        for i in page_obj],'page_count':paginator.num_pages
        }
        return Response(data)
        
class ImageHomeAPIView(APIView):
    def get(self,request):
        image_home=Image_home.objects.all()
        list_image_home=[{'image':i.image.url,'url':i.url_field} for i in image_home]
        data={'c':list_image_home}
        return Response(data)

class ProductInfoAPIVIew(APIView):
    def get(self,request):
        item_id=request.GET.get('item_id')
        media=request.GET.get('media')
        review_rating=request.GET.get('review_rating')
        comment=request.GET.get('comment')
        all_review=request.GET.get('all')
        review=request.GET.get('review')
        name=request.GET.get('name')
        shop=request.GET.get('shop')
        product_detail=request.GET.get('product_detail')
        review=request.GET.get('review')
        order=request.GET.get('order')
        from_item=request.GET.get('from_item')
        if item_id:
            item=Item.objects.get(id=item_id)
            if name and not order:
                shop=Shop.objects.filter(name=name)
                items=Item.objects.filter(shop__in=shop).order_by('-id')[:10]
                if from_item :
                    from_item=int(from_item)
                    to_item=from_item+10
                    items=Item.objects.filter(shop__in=shop).order_by('-id')[from_item:to_item]
                data={
                    'items':[{'item_info':i.item_info(),'item_image':item.media_upload.all()[0].upload_file(),'item_max':i.max_price(),'num_order':i.number_order(),
                    'item_url':i.get_absolute_url(),'voucher':i.get_voucher(),'item_min':i.min_price(),
                    'program_valid':i.count_program_valid(),'item_inventory':item.total_inventory()
                    } for i in items]}
                return Response(data)
            elif shop:
                data={'shop_logo':item.shop.logo.url,'shop_url':item.shop.get_absolute_url(),
                'shop_name':item.shop.name,
                'online':item.shop.user.shop.online,'num_follow':item.shop.num_follow(),
                'is_online':item.shop.user.shop.is_online,'count_product':item.shop.count_product(),
                'total_order':item.shop.total_order()}
                return Response(data)
            
            elif order and name:
                shop=Shop.objects.filter(name=name)
                orders=Order.objects.filter(shop__in=shop).order_by('-id')[:10]
                if from_item:
                    from_item=int(from_item)
                    to_item=from_item+10
                    orders=Order.objects.filter(shop__in=shop).order_by('-id')[from_item:to_item]
                data={
                    'list_orders':[{
                        'id':order.id,'shop':order.shop.name,'total':order.total_price(),'total_final':order.total_final(),
                        'order_item':[{'item_image':order_item.product.item.media_upload.all()[0].upload_file(),'item_url':order_item.product.item.get_absolute_url(),
                        'item_name':order_item.product.item.name,'color_value':order_item.product.get_color(),
                        'quantity':order_item.quantity,'percent_discount':order_item.product.percent_discount,
                        'size_value':order_item.product.get_size(),'price':order_item.product.price,
                        'total_price':order_item.final_price_item()
                        } for order_item in order.items.filter(check=True)]} for order in orders]
                    }
                return Response(data)
            elif review:
                list_review=ReView.objects.filter(orderitem__product__item=item)
                reviews=ReView.objects.filter(orderitem__product__item=item)
                count_comment= list_review.exclude(info_more='').count()
                count_media= list_review.exclude(media_upload=None).count()
                if review_rating:
                    reviews=reviews.filter(review_rating=review_rating)
                elif comment:
                    reviews=reviews.exclude(info_more='')
                elif media:
                    reviews=reviews.exclude(media_upload=None)
                paginator = Paginator(reviews, 10)  # Show 25 contacts per page.
                page_number = request.GET.get('page')
                page_obj = paginator.get_page(page_number)
                data={
                'reviews':[{'id':review.id,'review_text':review.review_text,'created':review.created,
                        'info_more':review.info_more,'rating_anonymous':review.anonymous_review,
                        'review_rating':review.review_rating,
                        'list_file':[{'file_id':file.id,'filetype':file.filetype(),'file':file.upload_file(),
                        'media_preview':file.media_preview(),'duration':file.duration,'show':False}
                        for file in review.media_upload.all()],'color_value':review.orderitem.product.get_color(),
                        'size_value':review.orderitem.product.get_size(),
                        'item_name':review.orderitem.product.item.name,
                        'user':review.user.username,'shop':review.shop_name(),
                        'url_shop':review.user.shop.get_absolute_url(),
                        } for review in page_obj],'page_count':paginator.num_pages,
                        'rating':[review.review_rating for review in list_review],'has_comment':count_comment,
                        'has_media':count_media
                        }
                return Response(data)
    def post(self, request, *args, **kwargs):
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token_obj = AccessToken(token)
        user_id=access_token_obj['user_id']
        item_id=request.POST.get('item_id')
        user=User.objects.get(id=user_id)
        item=Item.objects.get(id=item_id)
        like=True
        if user in item.liked.all():
            item.liked.remove(user)
            like=False
        else:
            item.liked.add(user)    
        data={'num_like':item.num_like(),'like':like}
        return Response(data)

class ShopinfoAPIVIew(APIView):
    def get(self,request):
        shop_name=request.GET.get('shop_name')
        page=request.GET.get('page')
        sort_price=request.GET.get('price_sort')
        minprice=request.GET.get('minprice')
        maxprice=request.GET.get('maxprice')
        rating_score=request.GET.get('rating_score')
        order=request.GET.get('order')
        sortBy=request.GET.get('sortBy')
        if shop_name:
            shop=Shop.objects.get(name=shop_name)
            items=Item.objects.filter(shop=shop)
            paginator = Paginator(items,30)  # Show 25 contacts per page.
            page_obj = paginator.get_page(1)
            if page:
                page_obj = paginator.get_page(page)
            list_page_item=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),
            'item_url':i.get_absolute_url(),'percent_discount':i.percent_discount(),'item_min':i.min_price(),
            'shop_city':i.shop.city,'item_brand':i.brand,'voucher':i.get_voucher(),
            'item_review':i.average_review(),'num_like':i.num_like(),'item_max':i.max_price(),
            'program_valid':i.count_program_valid(),'promotion':i.get_promotion(),
            'shock_deal':i.shock_deal_type(),'num_order':i.number_order()
            }
            for i in page_obj]
            data={
                'a':list_page_item,'page_count':paginator.num_pages
            }
            return Response(data)


@api_view(['GET', 'POST'])
def login_view(request):
    if request.method=="POST":
        username = request.data.get('username')
        password = request.data.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            data={'ok':'ok'}
            return Response(data)
        elif User.objects.filter(username = username).exists() and not User.objects.get(username=username).is_active:
            data={'errp':'ok'}
            return Response(data)
        else:
            data={'error':'ok'}
            return Response(data)

class ListItemRecommendAPIView(APIView):
    def get(self,request):
        items_recommend=Item.objects.all()
        page_number = request.GET.get('page')
        paginator = Paginator(items_recommend, 30)
        page_obj = paginator.get_page(page_number)
        list_items_recommend=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'item_max':i.max_price(),
        'percent_discount':i.percent_discount(),'item_min':i.min_price(),
        'program_valid':i.count_program_valid(),'item_url':i.get_absolute_url()
        }
        for i in page_obj]
        data={'d':list_items_recommend}
        return Response(data)

class ItemAPIView(APIView):
    def get(self,request):
        recently_viewed_products = None
        if 'recently_viewed' in request.session:
            products = Item.objects.filter(slug__in=request.session['recently_viewed'])
            recently_viewed_products = sorted(products, 
                key=lambda x: request.session['recently_viewed'].index(x.slug)
                )
            if len(request.session['recently_viewed']) > 6:
                request.session['recently_viewed'].pop()
        items=Item.objects.all()[0:30]
        list_items_recommend=[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),
            'item_max':i.max_price(),
            'item_url':i.get_absolute_url(),'percent_discount':i.percent_discount(),'item_min':i.min_price(),
            'num_order':i.number_order()
            }
            for i in items]
        data={
            'b':list_items_recommend,
            'recently_viewed_products': [{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),
            'item_max':i.max_price(),
            'item_url':i.get_absolute_url(),'percent_discount':i.percent_discount(),'item_min':i.min_price(),
            'num_order':i.number_order()
            }
            for i in recently_viewed_products],
        }
        return Response(data)

@api_view(['GET', 'POST'])
def save_voucher(request):
    if request.method=="POST":
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token_obj = AccessToken(token)
        user_id=access_token_obj['user_id']
        user=User.objects.get(id=user_id)
        voucher_id=request.POST.get('voucher_id')
        voucher=Vocher.objects.get(id=voucher_id)
        voucher.user.add(user)
        data={'ok':'ok'}
        return Response(data)

class CartAPIView(APIView):
    def get(self,request):
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token_obj = AccessToken(token)
        user_id=access_token_obj['user_id']
        user=User.objects.get(id=user_id)
        cart_item=OrderItem.objects.filter(ordered=False,user=user)[0:5]
        cart_items=OrderItem.objects.filter(ordered=False,user=user)
        count=cart_items.count()
        list_cart_item=[{'item_info':order_item.product.item.item_info(),'id':order_item.id,                'item_image':order_item.product.item.media_upload.all()[0].upload_file(),
                'item_url':order_item.product.item.get_absolute_url(),
                'price':order_item.product.price-order_item.product.total_discount(),
                'shock_deal_type':order_item.product.item.shock_deal_type(),
                'promotion':order_item.product.item.get_promotion(),
                } for order_item in cart_item]
        data={
            'count':count,
            'a':list_cart_item,
            'user_name':user.username,
            'image':user.shop.logo.url
            }
        return Response(data)

class UpdateCartAPIView(APIView):
    def get(self,request):
        item_id=request.GET.get('item_id')
        page = request.GET.get('page')
        item=Item.objects.get(id=item_id)
        items=Item.objects.filter(category=item.category)
        page_no=1
        paginator = Paginator(items,5)  # Show 25 contacts per page.
        page_obj = paginator.get_page(1)
        if page:
            page_obj = paginator.get_page(page)
            page_no=page
        data={
            'page_count':paginator.num_pages,'page':int(page_no),
            'list_item':[{'item_info':i.item_info(),
            'item_image':item.media_upload.all()[0].upload_file(),
            'percent_discount':i.percent_discount(),'item_min':i.min_price(),
            'shop_city':i.shop.city,'item_brand':i.brand,'voucher':i.get_voucher(),
            'item_review':i.average_review(),'num_like':i.num_like(),'item_max':i.max_price(),
            'promotion':i.get_promotion(),
            'shock_deal':i.shock_deal_type(),'num_order':i.number_order(),
            'item_url':i.get_absolute_url(),
            }
            for i in page_obj]
        }
        return Response(data)
    def post(self, request,price=0,total=0,count_orderitem=0,total_discount=0,discount_deal=0,discount_voucher=0,discount_promotion=0,count=0,*args, **kwargs):
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token_obj = AccessToken(token)
        user_id=access_token_obj['user_id']
        user=User.objects.get(id=user_id)
        item_id=request.POST.get('item_id')
        orderitem_id=request.POST.get('orderitem_id')
        color_id=request.POST.get('color_id')
        size_id=request.POST.get('size_id')
        byproduct_id=request.POST.get('byproduct_id')
        product=Variation.objects.all()
        data={}
        if item_id and size_id and color_id:
            color=Color.objects.get(id=color_id)
            size=Size.objects.get(id=size_id)
            product=Variation.objects.get(item=item_id,color=color,size=size)
        if item_id and color_id and not size_id:
            color=Color.objects.get(id=color_id)
            product=Variation.objects.get(item=item_id,color=color)
        if item_id and not color_id and size_id:
            size=Size.objects.get(id=size_id)
            product=Variation.objects.get(item=item_id,size=size)
        if item_id and not color_id:
            product=Variation.objects.get(item=item_id)
        if orderitem_id:
            order_item=OrderItem.objects.get(id=orderitem_id)
            order_item.product=product
            order_item.save()
            data.update({
            'id':order_item.id,'color_value':order_item.product.get_color(),'size_value':order_item.product.get_size(),
            'price':order_item.product.price,
            'total_price':order_item.total_discount_orderitem(),'inventory':order_item.product.inventory,'quantity':order_item.quantity,
            })
        if byproduct_id:
            byproduct=Byproductcart.objects.get(id=byproduct_id)
            byproduct.byproduct=product
            byproduct.save()
            data.update({ 
            'id':byproduct.id,'color_value':byproduct.byproduct.get_color(),'size_value':byproduct.byproduct.get_size(),
            'price':byproduct.byproduct.price,
            'size':byproduct.item.get_size(),
            'color':byproduct.item.get_color(),
            'total_price':byproduct.total_price(),
            'inventory':byproduct.byproduct.inventory,'quantity':byproduct.quantity,
            })
        order_check = Order.objects.filter(user=user, ordered=False).exclude(items=None)
        for order in order_check:
            discount_voucher+=order.discount_voucher()
            count_orderitem+=order.count_item_cart()
            for orderitem in order.items.all():
                count+=orderitem.count_item_cart()
                
                total+=orderitem.total_price_orderitem()
                total_discount+=orderitem.discount()
                discount_deal+=orderitem.discount_deal()
                discount_promotion+=orderitem.discount_promotion()  
        data.update({
            'total':total,'total_discount':total_discount,'discount_promotion':discount_promotion,
            'discount_deal':discount_deal,'discount_voucher':discount_voucher,'count':count,'count_orderitem':count_orderitem
        })
        return Response(data)

class AddToCardBatchAPIView(APIView):
    def get(self, request):
        item_id=request.GET.get('item_id')
        color_id=request.GET.get('color_id')
        size_id=request.GET.get('size_id')
        byproduct_id=request.GET.get('byproduct_id')
        product=Variation.objects.all()
        if item_id and color_id and size_id:
            color=Color.objects.get(id=color_id)
            size=Size.objects.get(id=size_id)
            product=Variation.objects.get(item=item_id,color=color,size=size)
        elif item_id and color_id and not size_id:
            color=Color.objects.get(id=color_id)
            product=Variation.objects.get(item=item_id,color=color)
        elif item_id and not color_id and size_id:
            size=Size.objects.get(id=size_id)
            product=Variation.objects.get(item=item_id,size=size)
        elif item_id and not size_id and not color_id:
            product=Variation.objects.get(item=item_id)
        
        data={'variation_id':product.id,'color_value':product.get_color(),'size_value':product.get_size(),
            'price':product.price,'discount_price':product.total_discount(),'inventory':product.inventory,
            }
        if byproduct_id:
            data.update({'byproduct_id':byproduct_id})
        return Response(data)
    def post(self, request, *args, **kwargs):
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token_obj = AccessToken(token)
        user_id=access_token_obj['user_id']
        user=User.objects.get(id=user_id)
        variation_id_choice=request.POST.get('variation_id_chocie')
        quantity_product=request.POST.get('quantity_product')
        item_id=request.POST.get('item_id')
        deal_id=request.POST.get('deal_id')
        variation_id=request.POST.getlist('variation_id')
        byproduct_id_delete=request.POST.getlist('byproduct_id_delete')
        Byproductcart.objects.filter(id__in=byproduct_id_delete).delete()
        list_quantity=request.POST.getlist('quantity')
        quantity_byproduct=request.POST.getlist('quantity_byproduct')
        byproduct_id=request.POST.getlist('byproduct_id')
        orderitem_id=request.POST.get('orderitem_id')
        variation_choice=Variation.objects.get(id=variation_id_choice)
        list_variation=Variation.objects.filter(id__in=variation_id)
        item=Item.objects.get(id=item_id)
        deal_shock=Buy_with_shock_deal.objects.get(id=deal_id)
        byproduct=Byproductcart.objects.filter(id__in=byproduct_id)
        for by in byproduct:
            for i in range(len(quantity_byproduct)):
                if list(byproduct).index(by)==i:
                    by.quantity=int(quantity_byproduct[i])
                    by.save()
        byproduct=Byproductcart.objects.bulk_create(
            [
            Byproductcart(user=user,byproduct=list_variation[i],quantity=int(list_quantity[i]))
            for i in range(len(variation_id))]
        )
        byproducts=Byproductcart.objects.order_by('-id')[:len(variation_id)]
        orderitem=OrderItem.objects.filter(id=orderitem_id)
        if orderitem.exists():
            orderitem_last=orderitem.last()
            orderitem_last.byproduct.add(*byproducts)
            orderitem_last.deal_shock=deal_shock
            orderitem_last.quantity=int(quantity_product)
            if orderitem_last.product!=variation_choice:
                orderitem_last.product=variation_choice
            orderitem_last.save()
            data={'o':'o'}
            return Response(data)
        else:
            orderitem=OrderItem.objects.create(
                product=variation_choice,
                user=user,
                ordered=False,
                shop=item.shop,
                deal_shock=deal_shock,
                quantity=int(quantity_product)
                )
            orderitem.byproduct.add(*byproducts)
            data={'o':'o'}
            return Response(data)

class AddToCartAPIView(APIView):
    def get(self,request):
        item_id=request.GET.get('item_id')
        color_id=request.GET.get('color_id')
        size_id=request.GET.get('size_id')
        product=Variation.objects.all()
        if item_id and color_id and size_id:
            color=Color.objects.get(id=color_id)
            size=Size.objects.get(id=size_id)
            product=Variation.objects.get(item=item_id,color=color,size=size)
        elif item_id and color_id and not size_id:
            color=Color.objects.get(id=color_id)
            product=Variation.objects.get(item=item_id,color=color)
        elif item_id and not color_id and size_id:
            size=Size.objects.get(id=size_id)
            product=Variation.objects.get(item=item_id,size=size)
        elif item_id and not size_id and not color_id:
            product=Variation.objects.get(item=item_id)
        data={
            'price':product.price,
            'percent_discout':product.percent_discount,
            'inventory':product.inventory,'id':product.id
            }
        return Response(data)

    def post(self, request, *args, **kwargs):
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token_obj = AccessToken(token)
        user_id=access_token_obj['user_id']
        user=User.objects.get(id=user_id)
        id=request.POST.get('id')
        item_id=request.POST.get('item_id')
        quantity=request.POST.get('quantity')
        item=Item.objects.get(id=item_id)
        product=Variation.objects.get(id=id)
        try:
            order_item=OrderItem.objects.get(
                product=product,
                user=user,
                ordered=False,
                shop=item.shop,
            )
            order_item.quantity =order_item.quantity+int(quantity)
            order_item.save()
            if order_item.quantity>order_item.product.inventory:
                order_item.quantity-=int(quantity)
                order_item.save()
                return Response({'eross':'over quantity'})
            else:
                data={'item_info':order_item.product.item.item_info(),'id':order_item.id,                'item_image':order_item.product.item.media_upload.all()[0].upload_file(),
                'item_url':order_item.product.item.get_absolute_url(),
                'price':order_item.product.price-order_item.product.total_discount(),
                'shock_deal_type':order_item.product.item.shock_deal_type(),
                'promotion':order_item.product.item.get_promotion(),
                }
                return Response(data)
        except Exception:
            order_item=OrderItem.objects.create(
                product=product,
                user=user,
                ordered=False,
                quantity=int(quantity),
                shop=item.shop,
                )
            data={
                'item_info':order_item.product.item.item_info(),'id':order_item.id,                'item_image':order_item.product.item.media_upload.all()[0].upload_file(),
                'item_url':order_item.product.item.get_absolute_url(),
                'price':order_item.product.price-order_item.product.total_discount(),
                'shock_deal_type':order_item.product.item.shock_deal_type(),
                'promotion':order_item.product.item.get_promotion(),
                }
            return Response(data)

class CartItemAPIView(APIView):
    def get(self,request):
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token_obj = AccessToken(token)
        user_id=access_token_obj['user_id']
        user=User.objects.get(id=user_id)
        list_order_item=OrderItem.objects.filter(user=user,ordered=False).order_by('-id')
        shops=Shop.objects.filter(shop_order__in=list_order_item).distinct()
        data={
            'user':{'user_id':user.id},
            'order_item':[{'id':order_item.id,'color_value':order_item.product.get_color(),'size_value':order_item.product.get_size(),
            'list_voucher':order_item.product.item.get_voucher(),'count_variation':order_item.product.item.count_variation(),
            'price':order_item.product.price,'discount_price':order_item.product.total_discount(),'shop_name':order_item.shop.name,
            'voucher_user':[True if user in voucher.user.all() else False for voucher in order_item.product.item.list_voucher()],
            'size':order_item.product.item.get_size(),'open':False,
            'item_image':order_item.product.item.media_upload.all()[0].upload_file(),
            'variation_url':order_item.product.get_absolute_url(),'byproduct':[{
            'id':byproduct.id,'color_value':byproduct.byproduct.get_color(),'size_value':byproduct.byproduct.get_size(),
            'color':byproduct.byproduct.item.get_color_deal(),'percent_discount_deal':byproduct.byproduct.percent_discount_deal_shock,
            'size':byproduct.byproduct.item.get_size_deal(),'price':byproduct.byproduct.price,
            'variation_id':byproduct.byproduct.id,'item_info':byproduct.byproduct.item.item_info(),
            'inventory':byproduct.byproduct.inventory,'quantity':byproduct.quantity,'item_url':byproduct.byproduct.item.get_absolute_url(),
            'count_program_valid':byproduct.byproduct.item.count_program_valid(),
            'total_price':byproduct.total_price(),'open':False,
            'item_image':byproduct.byproduct.item.media_upload.all()[0].upload_file(),
            'count_variation':byproduct.byproduct.item.count_variation(),
             } for byproduct in order_item.byproduct.all() if byproduct.byproduct.item.get_count_deal()>0],
            'color':order_item.product.item.get_color(),'item_info':order_item.product.item.item_info(),
            'item_url':order_item.product.item.get_absolute_url(),
            'count_program_valid':order_item.product.item.count_program_valid(),
            'promotion':order_item.product.item.get_promotion(),'check':order_item.check,
            'variation_id':order_item.product.id,'total_price':order_item.total_discount_orderitem(),
            'inventory':order_item.product.inventory,'quantity':order_item.quantity,
            'shock_deal_type':order_item.product.item.shock_deal_type(),
            } for order_item in list_order_item],'list_shop':[{'shop_user':shop.user.id,'shop_name':shop.name,'list_voucher_unique':[]} for shop in shops]
        }
        return Response(data,status=status.HTTP_200_OK)
    def post(self, request,count_orderitem=0,price=0,total=0,total_discount=0,discount_deal=0,discount_voucher=0,discount_promotion=0,count=0, *args, **kwargs):
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token_obj = AccessToken(token)
        user_id=access_token_obj['user_id']
        user=User.objects.get(id=user_id)
        byproduct_id_delete=request.POST.get('byproduct_id_delete')
        byproduct_id=request.POST.get('byproduct_id')
        orderitem_id=request.POST.get('orderitem_id')
        orderitem_id_delete=request.POST.get('orderitem_id_delete')
        quantity=request.POST.get('quantity')
        shop_name=request.POST.getlist('shop_name')
        id_checked=request.POST.getlist('id_checked')
        id_check=request.POST.getlist('id_check')
        voucher_id=request.POST.get('voucher_id')
        voucher_id_remove=request.POST.get('voucher_id_remove')
        shops=Shop.objects.filter(name__in=shop_name).distinct()
        order_qs = Order.objects.filter(user=user,ordered=False,shop__in=shops).distinct()
        list_shop=[shop.name for shop in shops]
        list_shop_order=[]
        OrderItem.objects.filter(id__in=id_checked).update(check=True)
        OrderItem.objects.filter(id__in=id_check).update(check=False)
        ordered_date = timezone.now()
        discount_voucher_shop=0
        if shop_name:
            if order_qs.count()>0:
                for order in order_qs:
                    if voucher_id:
                        voucher=Vocher.objects.get(id=voucher_id)
                        if voucher.shop.name==order.shop.name:
                            order.vocher=voucher
                            discount_voucher_shop=order.discount_voucher()
                            order.save()
                    if voucher_id_remove:
                        voucher=Vocher.objects.get(id=voucher_id_remove)
                        if voucher.shop.name==order.shop.name:
                            order.vocher=None
                            order.save()
                    list_shop_order.append(order.shop.name)
                    list_order_item_remove=OrderItem.objects.filter(shop=order.shop,id__in=id_check)
                    order.items.remove(*list_order_item_remove)
                    list_order_item_add=OrderItem.objects.filter(shop=order.shop,id__in=id_checked)
                    order.items.add(*list_order_item_add) 
                list_shop_remainder=list(set(list_shop) - set(list_shop_order))
                if len(list_shop_remainder)>0:
                    list_shop_remain=Shop.objects.filter(name__in=list_shop_remainder)
                    order = Order.objects.bulk_create([
                    Order(
                        user=user, ordered_date=ordered_date,shop=shop) for shop in list_shop_remain]
                        )
                    orders=Order.objects.filter(user=user).order_by('-id')[:len(list_shop_remain)]
                    for order in orders:
                        list_order_item=OrderItem.objects.filter(shop=order.shop,id__in=id_checked)
                        order.items.add(*list_order_item)
            else:    
                order = Order.objects.bulk_create([
                    Order(
                    user=user, ordered_date=ordered_date,shop=shop) for shop in shops]
                )
                order_s=Order.objects.filter(ordered=False,user=user)
                for order in order_s:
                    list_order_item=OrderItem.objects.filter(shop=order.shop,id__in=id_checked)
                    order.items.add(*list_order_item)
        else:
            if byproduct_id_delete:
                Byproductcart.objects.get(id=byproduct_id_delete).delete()
            elif byproduct_id :
                byproduct=Byproductcart.objects.get(id=byproduct_id)
                byproduct.quantity=int(quantity)
                byproduct.save()
                price=byproduct.total_price()
            elif orderitem_id:
                orderitem=OrderItem.objects.get(id=orderitem_id)
                orderitem.quantity=int(quantity)
                orderitem.save()
                price=orderitem.total_discount_orderitem()
            else:
                OrderItem.objects.get(id=orderitem_id_delete).delete()
                Byproductcart.objects.filter(orderitem=None).delete()
        order_check = Order.objects.filter(user=user, ordered=False).exclude(items=None)
        for order in order_check:
            discount_voucher+=order.discount_voucher()
            count_orderitem+=order.count_orderitem()
            for orderitem in order.items.all():
                count+=orderitem.count_item_cart()
                total+=orderitem.total_price_orderitem()
                total_discount+=orderitem.discount()
                discount_deal+=orderitem.discount_deal()
                discount_promotion+=orderitem.discount_promotion()
        data={
            'discount_voucher_shop':discount_voucher_shop,
            'price':price,'count':count,'total':total,'discount_deal':discount_deal,
            'total_discount':total_discount,'count_orderitem':count_orderitem,
            'discount_promotion':discount_promotion,'discount_voucher':discount_voucher
            }
        return Response(data)

class OrderAPIView(APIView):
    def get(self,request):
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token_obj = AccessToken(token)
        user_id=access_token_obj['user_id']
        user=User.objects.get(id=user_id)
        order_check = Order.objects.filter(user=user, ordered=False).exclude(items=None)
        threads = Thread.objects.filter(participants=user).order_by('timestamp')
        data={
        'list_threads':[{'id':thread.id,'count_message':thread.count_message(),'list_participants':[user.id for user in thread.participants.all() ]} for thread in threads],
        'orders':[{'discount_voucher_shop':order.discount_voucher(),'total':order.total_price_order(),
            'discount_deal':order.discount_deal(),'count':order.count_item_cart(),
            'count_orderitem':order.count_orderitem(),'shop_name':order.shop.name,
            'discount_promotion':order.discount_promotion(),'total_discount':order.discount(),
            'voucher':order.get_voucher()} 
            for order in order_check]
        }
        return Response(data,status=status.HTTP_200_OK)

@api_view(['GET', 'POST'])
def get_city(request):
    list_city=City.objects.all()
    data={'a':list_city.values()}
    return Response(data)

class AddressAPIView(APIView):
    def get(self,request):
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token_obj = AccessToken(token)
        user_id=access_token_obj['user_id']
        user=User.objects.get(id=user_id)
        addresses = Address.objects.filter(user=user)
        data={'a':list(addresses.values()),'user':{'image':user.shop.image.url,'name':user.username}}
        return Response(data)
    def post(self, request, *args, **kwargs):
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token_obj = AccessToken(token)
        user_id=access_token_obj['user_id']
        user=User.objects.get(id=user_id)
        city=request.POST.get('city')
        district=request.POST.get('district')
        town=request.POST.get('town')
        phone_number=request.POST.get('phone_number')
        name=request.POST.get('name')
        address_choice=request.POST.get('address_choice')
        address_detail=request.POST.get('address')
        address_type=request.POST.get('address_type')
        default=request.POST.get('default')
        id=request.POST.get('id')
        update=request.POST.get('update')
        default_address=False
        if default=='true':
            default_address=True
        if id:
            address=Address.objects.get(id=id)
            if update:
                address.address_choice=address_choice
                address.default=default_address
                address.name=name
                address.phone_number=phone_number
                address.city=city
                address.address_type=address_type
                address.address=address_detail
                address.town=town
                address.district=district
                address.save()
            elif default:
                address.default=True
                address.save()
                Address.objects.exclude(id=address.id).update(default=False)
            else:
                address.delete()
                data={'pk':'pk'}
                return Response(data)
            data={
                'id':address.id,'default':address.default,'district':address.district,'town':address.town,
                'name':address.name,'phone_number':address.phone_number,'city':address.city,'address':address.address
            }
            return Response(data)
        else:
            address,created=Address.objects.get_or_create(
                user=user,
                address_choice=address_choice,
                default=default_address,
                name=name,
                phone_number=phone_number,
                city=city,
                town=town,
                district=district,
                address_type=address_type,
                address=address_detail
            )
            if address.default==True:
                Address.objects.exclude(id=address.id).update(default=False)
            data={
                'id':address.id,'default':address.default,'district':address.district,'town':address.town,
                'name':address.name,'phone_number':address.phone_number,'city':address.city,'address':address.address
            }
            return Response(data)

class CheckoutAPIView(APIView):
    def get(self,request):
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token_obj = AccessToken(token)
        user_id=access_token_obj['user_id']
        user=User.objects.get(id=user_id)
        address=Address.objects.filter(user=user,default=True)
        orders = Order.objects.filter(user=user, ordered=False).exclude(items=None)
        threads = Thread.objects.filter(participants=user).order_by('timestamp')
        list_orders=[{'shop':order.shop.name,'discount_voucher':order.discount_voucher(),
        'total':order.total_price_order(),'total_final':order.total_final_order(),
        'count':order.count_item_cart(),'fee_shipping':order.fee_shipping(),
        'discount_promotion':order.discount_promotion(),'total_discount':order.total_discount_order(),
        'order_item':[{'item_info':order_item.product.item.item_info(),'item_url':order_item.product.item.get_absolute_url(),
        'color_value':order_item.product.get_color(),'size_value':order_item.product.get_size(),
        'item_image':order_item.product.item.media_upload.all()[0].upload_file(),
        'byproduct':[{
            'color_value':byproduct.byproduct.get_color(),'size_value':byproduct.byproduct.get_size(),
            'price':byproduct.byproduct.price,
            'item_image':byproduct.byproduct.item.media_upload.all()[0].upload_file(),
            'item_info':byproduct.byproduct.item.item_info(),
            'quantity':byproduct.quantity,'item_url':byproduct.byproduct.item.get_absolute_url(),
            'count_program_valid':byproduct.byproduct.item.count_program_valid(),
            'total_price':byproduct.total_price(),
             } for byproduct in order_item.byproduct.all()],
        'quantity':order_item.quantity,'discount_price':order_item.product.total_discount(),
        'price':order_item.product.price,
        'total_price':order_item.total_discount_orderitem()
        } for order_item in order.items.all()]} for order in orders]
        data={
            'a':list_orders,'c':list(address.values()),'user':{'user_id':user.id},
            'list_threads':[{'id':thread.id,'count_message':thread.count_message(),'list_participants':[user.id for user in thread.participants.all() ]} for thread in threads]
        }
        return Response(data)
    def post(self, request, *args, **kwargs):
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token_obj = AccessToken(token)
        user_id=access_token_obj['user_id']
        user=User.objects.get(id=user_id)
        id=request.POST.get('id')
        address=Address.objects.get(id=id)
        payment_option=request.POST.get('payment_choice')
        total=0
        orders = Order.objects.filter(user=user, ordered=False).exclude(items=None)
        if payment_option == 'Paypal':
            payment=Payment.objects.create(user=user,payment_method="P",
            amount=total,paid=False
            )
            payment.order.add(*orders)
            data={'a':'a'}
            return Response(data)
        else:
            for order in orders:
                order.shipping_address = address
                order.ordered=True
                order.amount=order.total_discount_order()
                order.ref_code = create_ref_code()
                order.ordered_date=timezone.now()
                order.payment_choice=payment_option
                items = order.items.all()
                items.update(ordered=True) 
                for item in items:
                    item.save()   
                    products=Variation.objects.get(orderitem=item.id)
                    products.inventory -= item.quantity
                    products.save()
            bulk_update(orders)
            data={'a':'a'}
            return Response(data)

@api_view(['GET', 'POST'])
def payment_complete(request): 
    token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
    access_token_obj = AccessToken(token)
    user_id=access_token_obj['user_id']
    user=User.objects.get(id=user_id) 
    if request.method=="POST":
        pay_id=request.POST.get('payID')
        payment=Payment.objects.filter(paid=False,user=user).last()
        payment.payment_number=pay_id
        payment.paid=True
        payment.save()
        list_orders = Order.objects.filter(user=user, ordered=False)
        for order in list_orders:
            order.ordered=True
            order.amount=order.total_final_order()
            order.ref_code = create_ref_code()
            order.ordered_date=timezone.now()
            order.payment_choice="Paypal"
            order.payment_number=pay_id
            items = order.items.all()
            items.update(ordered=True) 
            for item in items:
                item.save()   
                products=Variation.objects.get(orderitem=item.id)
                products.inventory -= item.quantity
                products.save()
                for byproduct in item.byproduct.all():
                    product=Variation.objects.get(byproductcart=byproduct)
                    product.inventory -= byproduct.quantity
                    product.save()
        bulk_update(list_orders)
        Payment.objects.filter(paid=False,user=user).delete()
        return Response({'ok':'ok'})
    else:
        orders = Order.objects.filter(user=user, ordered=False)
        amount=0
        for order in orders:
            amount+=order.total_final_order()
        return Response({'amount':amount})  

class DealShockAPIView(APIView):
    def get(self,request,id):
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token_obj = AccessToken(token)
        user_id=access_token_obj['user_id']
        user=User.objects.get(id=user_id)
        variation=Variation.objects.get(id=id)
        quantity=1
        orderitem_id=0
        order_item=[]
        list_product=[]
        variation_info={'variation_id':variation.id,'color_value':variation.get_color(),'size_value':variation.get_size(),
            'quantity':quantity,'item_info':variation.item.item_info(),'check':True,'main':True,
            'price':variation.price,'discount_price':variation.total_discount(),'item_url':variation.item.get_absolute_url(),
            'size':variation.item.get_size(),'inventory':variation.inventory,'show':False,
            'item_image':variation.item.media_upload.all()[0].upload_file(),
            'color':variation.item.get_color()}
        list_product.append(variation_info)
        orderitem=OrderItem.objects.filter(product=variation,ordered=False,user=user)
        if orderitem.exists():
            orderitem_last=orderitem.last()
            quantity=orderitem_last.quantity
            orderitem_id=orderitem_last.id
            for byproduct in orderitem_last.byproduct.all():
                order_item.append({'variation_id':byproduct.byproduct.id,'color_value':byproduct.byproduct.get_color(),
                'quantity':byproduct.quantity,'size_value':byproduct.byproduct.get_size(),'item_info':byproduct.byproduct.item.item_info(),
                'discount_price':byproduct.byproduct.total_discount(),'byproduct_id':byproduct.id})
        item=Item.objects.get(variation=variation)
        shock_deal=Buy_with_shock_deal.objects.get(main_product=item,valid_to__gt=datetime.datetime.now()-datetime.timedelta(seconds=10))
        byproducts=shock_deal.byproduct.all()
        for item in byproducts:
            if item.get_count_deal()>0:
                list_product.append({
                    'item_info':item.item_info(),'size':item.get_size_deal(),
                    'color':item.get_color_deal(),'get_count_deal':item.get_count_deal(),
                    'color_value':'','quantity':1,'size_value':'',
                    'price':item.max_price(),'show':False,
                    'item_image':item.media_upload.all()[0].upload_file(),
                    'check':False,'main':False,'item_url':item.get_absolute_url(),
                    })
        
        for i in range(len(list_product)):
            for j in range(len(order_item)):
                if list_product[i]['item_info']==order_item[j]['item_info'] and list_product[i]['main']==False:
                    list_product[i]['variation_id']=order_item[j]['variation_id']
                    list_product[i]['color_value']=order_item[j]['color_value']
                    list_product[i]['size_value']=order_item[j]['size_value']
                    list_product[i]['quantity']=order_item[j]['quantity']
                    list_product[i]['discount_price']=order_item[j]['discount_price']
                    list_product[i]['check']=True
                    list_product[i]['byproduct_id']=order_item[j]['byproduct_id']
        
        data={
            'orderitem_id':orderitem_id,'deal_id':shock_deal.id,
            'list_product':list_product
        }
        return Response(data)

class PromotionAPIView(APIView):
    def get(self,request,id):
        promotion=Promotion_combo.objects.get(id=id)
        items=promotion.product.all()
        data={
            'promotion_id':promotion.id,'combo_type':promotion.combo_type,
            'discount_percent':promotion.discount_percent,
            'discount_price':promotion.discount_price,
            'price_special_sale':promotion.price_special_sale,
            'quantity_to_reduced':promotion.quantity_to_reduced,
            'list_items':[{
            'item_info':item.item_info(),
            'item_image':item.media_upload.all()[0].upload_file(),
            'item_url':item.get_absolute_url(),'max_price':item.max_price(),
            'count_program_valid':item.count_program_valid(),'min_price':item.min_price(),
            'size':item.get_size(),'color':item.get_color(),'inventory':item.total_inventory()} for item in items]
        }
        return Response(data)

class MessageAPIView(APIView):
    def get(self,request):
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token_obj = AccessToken(token)
        user_id=access_token_obj['user_id']
        user=User.objects.get(id=user_id)
        threads = Thread.objects.filter(participants=user).order_by('timestamp')
        data = {'user':{'username':user.username,'user_id':user.id},
            'threads':[{
            'message':[{'read':message.seen,'sender':message.user.username}
            for message in thread.chatmessage_thread.all().order_by('-id')[:1]]}
            for thread in threads]
        }
        return Response(data)

class ListThreadAPIView(APIView):
    def get(self,request):
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token_obj = AccessToken(token)
        user_id=access_token_obj['user_id']
        user=User.objects.get(id=user_id)
        thread_id=request.GET.get('thread_id')
        offset=request.GET.get('offset')
        shop_name=request.GET.get('shop_name')
        item=request.GET.get('item')
        order=request.GET.get('order')
        list_thread=request.GET.get('list_thread')
        limit=10
        threads = Thread.objects.filter(participants=user)
        if thread_id:
            thread=Thread.objects.get(id=thread_id)
            messages=Message.objects.filter(thread=thread)
            message_count=messages.count()
            to_item=message_count
            if offset:
                to_item=message_count-int(offset)
            from_item=to_item-limit
            if to_item-limit<=0:
                from_item=0
            if from_item<to_item:
                messages=messages[from_item:to_item]
            data={
            'messages':[{'text':message.message,
                'sender':message.user.username,'created':message.date_created,
                'message_order':message.message_order(),'message_product':message.message_product(),
                'list_file':[{'file':uploadfile.file.url,'file_name':uploadfile.filename(),
                'file_preview':uploadfile.file_preview(),'duration':uploadfile.duration,'filetype':uploadfile.filetype()}
                for uploadfile in message.file.all()
                ]} for message in messages]
                }
        
            if list_thread:
                data.update({
                    'threads':[{'id':thread.id,'info_thread':thread.info_thread(),
                    'count_message_not_seen':thread.count_message_not_seen(),'count_message':thread.count_message(),
                    'message':[{'text':message.message,'file':message.message_file(),'read':message.seen,'sender':message.user.username,
                    'created':message.date_created,'message_order':message.message_order(),'message_product':message.message_product(),
                    'list_file':[{'filetype':uploadfile.filetype()}
                    for uploadfile in message.file.all()]}
                    for message in thread.chatmessage_thread.all().order_by('-id')[:1]]}
                    for thread in threads]
                })
            return Response(data)

        elif shop_name:
            shop=Shop.objects.get(name=shop_name)
            if item:
                to_item=shop.count_product()
                if offset:
                    to_item=int(offset)
                from_item=to_item-5
                list_items=Item.objects.filter(shop=shop).order_by('-id')[from_item:to_item]
                data={'count_product':shop.count_product(),
                    'list_items':[{'item_name':i.name,'item_image':i.media_upload.all()[0].upload_file(),'number_order':i.number_order(),
                    'item_id':i.id,'item_inventory':i.total_inventory(),'item_max':i.max_price(),
                    'item_min':i.min_price()
                    } for i in list_items]
                }
                return Response(data)
            else:
                count_order=Order.objects.filter(shop=shop,user=user,ordered=True).count()
                to_item=count_order
                if offset:
                    to_item=int(offset)
                from_item=to_item-5
                list_orders=Order.objects.filter(shop=shop,user=user).order_by('-id')[from_item:to_item]
                data={'count_order':count_order,
                    'list_orders':[{
                    'id':order.id,'shop':order.shop.name,'total_final_order':order.total_final_order(),
                    'count_item':order.count_item_cart(),
                    'order_item':[{'item_image':order_item.product.item.media_upload.all()[0].upload_file(),'item_url':order_item.product.item.get_absolute_url(),
                    'item_name':order_item.product.item.name,'color_value':order_item.product.get_color(),
                    'quantity':order_item.quantity,'discount_price':order_item.product.total_discount(),
                    'size_value':order_item.product.get_size(),'price':order_item.product.price,
                    'total_price':order_item.total_discount_orderitem()
                    } for order_item in order.items.all()]} for order in list_orders]
                }
                return Response(data)
        else:
            data = {
            'threads':[{'id':thread.id,'info_thread':thread.info_thread(),
            'count_message_not_seen':thread.count_message_not_seen(),'count_message':thread.count_message(),
            'message':[{'text':message.message,'file':message.message_file(),'read':message.seen,'sender':message.user.username,
            'created':message.date_created,'message_order':message.message_order(),'message_product':message.message_product(),
            'list_file':[{'filetype':uploadfile.filetype()}
            for uploadfile in message.file.all()]}
            for message in thread.chatmessage_thread.all().order_by('-id')[:1]]}
            for thread in threads]
            }
            return Response(data)
    def post(self, request, *args, **kwargs):
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token_obj = AccessToken(token)
        user_id=access_token_obj['user_id']
        user=User.objects.get(id=user_id)
        participants=request.POST.getlist('participants')
        thread_id=request.POST.get('thread_id')
        group_name=request.POST.get('group_name')
        seen=request.POST.get('seen')
        item_id=request.POST.get('item_id')
        order_id=request.POST.get('order_id')
        if thread_id and seen:
            thread=Thread.objects.get(id=thread_id)
            messages=Message.objects.filter(thread=thread)
            messages.update(seen=True)
            message_count=messages.count()
            messages=messages[message_count-10:message_count]
            data={
            'messages':[{'text':message.message,'file':message.message_file(),'filetype':message.message_filetype(),
                'sender':message.user.username,'created':message.date_created,
                'message_order':message.message_order(),'message_product':message.message_product(),
                'list_file':[{'file':uploadfile.file.url,'file_name':uploadfile.filename(),
                'file_preview':uploadfile.file_preview(),'duration':uploadfile.duration,'filetype':uploadfile.filetype()}
                for uploadfile in message.file.all()
                ]} for message in messages
                ]
            }
            return Response(data)
        elif  participants and order_id:
            list_user=User.objects.filter(id__in=participants)
            thread=Thread.objects.create(
            group_name=group_name
            )
            thread.participants.add(*list_user)
            if order_id:
                order=Order.objects.get(id=order_id)
                message,created=Message.objects.get_or_create(
                order=order,user=user
                )
            elif item_id:
                item=Item.objects.get(id=item_id)
                message,created=Message.objects.get_or_create(
                product=item,user=user
                )
        
            threads=Thread.objects.filter(participants=user).order_by('-id')
            messages=Message.objects.filter(thread=thread)
            message_count=messages.count()
            to_item=message_count
            from_item=to_item-10
            if to_item-10<=message_count:
                from_item=0
            if from_item<to_item:
                messages=messages[from_item:to_item]
            data={'threadchoice':{'id':thread.id,'count_message':thread.count_message()},
            'messages':[{'text':message.message,
            'sender':message.user.username,'created':message.date_created,
            'message_order':message.message_order(),'message_product':message.message_product(),
            'list_file':[{'file':uploadfile.file.url,'file_name':uploadfile.filename(),
            'file_preview':uploadfile.file_preview(),'duration':uploadfile.duration,'filetype':uploadfile.filetype()}
            for uploadfile in message.file.all()
            ]} for message in messages],
            'threads':[{'id':thread.id,'info_thread':thread.info_thread(),
            'count_message_not_seen':thread.count_message_not_seen(),'count_message':thread.count_message(),
            'message':[{'text':message.message,'file':message.message_file(),'read':message.seen,'sender':message.user.username,
            'created':message.date_created,'message_order':message.message_order(),'message_product':message.message_product(),
            'list_file':[{'filetype':uploadfile.filetype()}
            for uploadfile in message.file.all()]}
            for message in thread.chatmessage_thread.all().order_by('-id')[:1]]}
            for thread in threads]
            }
            
            return Response(data)

class ThreadAPIView(APIView):
    def get(self,request):
        thread_id=request.GET.get('thread_id')
        if thread_id:
            thread=Thread.objects.get(id=thread_id)
            messages=Message.objects.filter(thread=thread)
            message_count=messages.count()
            messages=messages[message_count-10:message_count]
            data={
            'messages':[{'text':message.message,'file':message.message_file(),'filetype':message.message_filetype(),
                'user_id':message.user.id,'created':message.date_created,'item':[{'item_name':item.name,
                'item_image':item.media_upload.all()[0].upload_file(),'item_url':item.get_absolute_url(),'item_max':item.max_price(),
                'item_min':item.min_price(),'percent_discount':item.percent_discount()
                } for item in Item.objects.filter(message=message)],
                'message_order':message.message_order(),'message_product':message.message_product(),
                'list_file':[{'file':uploadfile.file.url,'file_name':uploadfile.filename(),
                'file_preview':uploadfile.file_preview(),'duration':uploadfile.duration,'filetype':uploadfile.filetype()}
                for uploadfile in message.file.all()
                ]} for message in messages
                ]
            }
            return Response(data)
    def post(self, request, *args, **kwargs):
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token_obj = AccessToken(token)
        user_id=access_token_obj['user_id']
        user=User.objects.get(id=user_id)
        item=Item.objects.all()
        count=item.count()
        sender=user
        user=user
        thread=Thread.objects.filter(sender=user)
        receiver=request.POST.get('id')
        thread_id=request.POST.get('thread_id')
        seen=request.POST.get('seen')
        receive=User.objects.get(id=receiver)
        if Thread.objects.filter(sender=user,receiver=receive).exists():
            thread=Thread.objects.filter(sender=user,receiver=receive).first()
        elif Thread.objects.filter(sender=receive,receiver=user).exists():
            thread=Thread.objects.filter(sender=receive,receiver=user).first()
        elif thread_id:
            thread=Thread.objects.get(id=thread_id)
            Message.objects.filter(thread=thread,seen=False).update(seen=True)
        else:
            thread,created=Thread.objects.get_or_create(
                sender=sender,
                receiver=receive,
            )
        threads=Thread.objects.filter(Q(sender=user) | Q(receiver=user)).order_by('-id')
        messages=Message.objects.filter(thread=thread)
        message_count=messages.count()
        messages=messages[message_count-10:message_count]
        data={'count':count,
            'thread':thread.id,'sender':thread.sender.id,'receiver':thread.receiver.id,
            'messages':[{'text':message.message,'file':message.message_file(),'filetype':message.message_filetype(),
            'user_id':message.user.id,'created':message.date_created,'item':message.message_product(),
            'message_order':message.message_order(),
            'list_file':[{'file':uploadfile.file.url,'filename':uploadfile.filename(),
            'file_preview':uploadfile.file_preview(),'duration':uploadfile.duration,'filetype':uploadfile.filetype()}
            for uploadfile in message.file.all()
            ]} for message in messages
            ],
            'threads':[{'thread_id':thread.id,'sender':thread.sender.username,'receiver':thread.receiver.username,
            'shop_name_sender':thread.shop_name_sender(),'shop_logo_sender':thread.shop_logo_sender(),
            'count_message_not_seen':thread.count_message_not_seen(),'sender_id':thread.sender.id,
            'receiver_id':thread.receiver.id,
            'shop_name_receiver':thread.shop_name_receiver(),'shop_logo_receiver':thread.shop_logo_receiver(),
            'messages':[{'text':message.message,'file':message.message_file(),'created':message.date_created,
            'message_order':message.message_order(),'message_product':message.message_product(),
            'message_filetype':message.message_filetype(),
            'user_id':message.user.id} for message in thread.chatmessage_thread.all().order_by('-id')[:1]
            ]} for thread in threads
            ]
        }
        
        return Response(data)

@api_view(['GET', 'POST'])
def upload_file(request):
    token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
    access_token_obj = AccessToken(token)
    user_id=access_token_obj['user_id']
    user=User.objects.get(id=user_id)
    if request.method=="POST":
        file_id=request.POST.get('file_id')
        file=request.FILES.getlist('file')
        file_preview=request.FILES.getlist('file_preview')
        duration=request.POST.getlist('duration')
        name=request.POST.getlist('name')
        media_preview=[None for  i in range(len(file))]
        list_duration=[0 for  i in range(len(file))]
        for i in range(len(media_preview)):
            for j in range(len(file_preview)):
                if i==j:
                    media_preview[i]=file_preview[j]
        
        if file_id:
            UploadFile.objects.get(id=file_id).delete()
            data={
                'seen':'seen'
            }
            return Response(data)
        elif file:
            upload_files=UploadFile.objects.bulk_create([
            UploadFile(
            file=file[i],
            file_name=name[i],
            image_preview=media_preview[i],
            duration=list_duration[i],
            upload_by=user)
            for i in range(len(file))])
            data={
               'list_file':[{'id':upload_file.id,'file':upload_file.file.url,'filename':upload_file.file_name,
               'file_preview':upload_file.file_preview(),'filetype':upload_file.filetype(),'duration':upload_file.duration
               } for upload_file in upload_files] 
            }
            return Response(data)

@api_view(['GET', 'POST'])
def update_message(request):
    if request.method=="POST":
        thread_id=request.POST.get('thread_id')
        seen=request.POST.get('seen')
        thread=Thread.objects.get(id=thread_id)
        Message.objects.filter(thread=thread,seen=False).update(seen=True)
        messages=Message.objects.filter(thread=thread).order_by('-id')[:10]
        data={
            'messages':[{'text':message.message,'file':message.message_file(),'filetype':message.message_filetype(),
            'user_id':message.user.id,'created':message.date_created,'item':message.message_product(),
            'message_order':message.message_order(),
            'list_file':[{'file':uploadfile.file.url,'file_name':uploadfile.filename(),
            'file_preview':uploadfile.file_preview(),'duration':uploadfile.duration,'filetype':uploadfile.filetype()}
            for uploadfile in message.file.all()
            ]} for message in messages]
            }
        return Response(data)

class ProfileAPIView(APIView):
    def get(self,request):
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token_obj = AccessToken(token)
        user_id=access_token_obj['user_id']
        user=User.objects.get(id=user_id)
        shop_name=None
        shop_logo=None
        count_product=0
        if Shop.objects.filter(user=user).exists():
            shop_name=Shop.objects.filter(user=user).first().name
            shop_logo=Shop.objects.filter(user=user).first().logo.url
            count_product=Shop.objects.filter(user=user).first().count_product()
        data={
            'username':user.username,'name':user.shop.name,'email':user.email,'user_id':user.id,
            'phone_number':user.shop.phone_number,'date_of_birth':user.shop.date_of_birth,
            'image':user.shop.image.url,'shop_name':shop_name,'shop_logo':shop_logo,
            'gender':user.shop.get_gender_display(),'user_id':user.id,'count_product':count_product,
            }
        return Response(data)
        
@api_view(['GET', 'POST'])
def get_address(request):
    token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
    access_token_obj = AccessToken(token)
    user_id=access_token_obj['user_id']
    user=User.objects.get(id=user_id)
    addresses = Address.objects.filter(user=user)
    data={'a':list(addresses.values()),'user':{'image':user.shop.image.url,'name':user.username}}
    return Response(data)

class PurchaseAPIView(APIView):
    def get(self,request):
        limit=5
        from_item=0
        offset=request.GET.get('offset')
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token_obj = AccessToken(token)
        user_id=access_token_obj['user_id']
        user=User.objects.get(id=user_id)
        threads = Thread.objects.filter(participants=user).order_by('timestamp')
        order_id=request.GET.get('id')
        review=request.GET.get('review')
        if order_id and not review:
            order = Order.objects.get(id=order_id)
            data={
                'order_item':[{
                'item_image':order_item.product.item.media_upload.all()[0].upload_file(),'item_url':order_item.product.item.get_absolute_url(),
                'item_name':order_item.product.item.name,'color_value':order_item.product.get_color(),
                'size_value':order_item.product.get_size(),'id':order_item.id
                } for order_item in order.items.all()],'username':user.username
            }
            return Response(data)
        elif order_id and review:
            order = Order.objects.get(id=order_id)
            orderitem=order.items.all()
            reviews=ReView.objects.filter(orderitem__in=orderitem)
            data={
                'list_review':[{'id':review.id,'review_text':review.review_text,'created':review.created,
                'info_more':review.info_more,'rating_anonymous':review.anonymous_review,'list_file':[{'filetype':file.filetype(),'file':file.upload_file(),
                'media_preview':file.media_preview(),'duration':file.duration,'file_id':file.id,'show':False}
                 for file in review.media_upload.all()],
                'rating_bab_category':[review.rating_product,review.rating_seller_service,review.rating_shipping_service],
                'review_rating':review.review_rating,'edited':review.edited,
                'item_image':review.orderitem.product.item.media_upload.all()[0].upload_file(),'item_url':review.orderitem.product.item.get_absolute_url(),
                'item_name':review.orderitem.product.item.name,'color_value':review.orderitem.product.get_color(),
                'size_value':review.orderitem.product.get_size()
                } for review in reviews],'username':user.username
            }
            return Response(data)
        else:
            if offset:
                from_item=int(offset)
            to_item=from_item+limit
            order_all = Order.objects.filter(ordered=True,user=user).order_by('-id')
            count_order=order_all.count()
            orders = Order.objects.filter(ordered=True,user=user).order_by('-id')[from_item:to_item]
            list_order=[{'shop_name':order.shop.name,'shop_user':order.shop.user.id,'received':order.received,'canceled':order.canceled,
                'being_delivered':order.being_delivered,'shop_url':order.shop.get_absolute_url(),'id':order.id,
                'order_url':order.get_absolute_url(),'accepted':order.accepted,'amount':order.total_final_order(),
                'received_date':order.received_date,'review':order.count_review(),
                'order_item':[{
                'item_image':order_item.product.item.media_upload.all()[0].upload_file(),'item_url':order_item.product.item.get_absolute_url(),
                'item_name':order_item.product.item.name,'color_value':order_item.product.get_color(),
                'quantity':order_item.quantity,'discount_price':order_item.product.total_discount(),
                'size_value':order_item.product.get_size(),'price':order_item.product.price,
                'id':order_item.id
                } for order_item in order.items.all()]} for order in orders]
            data={
                'user':{'image':user.shop.image.url,'name':user.username,'user_id':user.id},
                'a':list_order,'count_order':count_order,
                'list_threads':[{'id':thread.id,'count_message':thread.count_message(),'list_participants':[user.id for user in thread.participants.all() ]} for thread in threads]
                }
            return Response(data)
    def post(self,request,*args, **kwargs):
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        access_token_obj = AccessToken(token)
        user_id=access_token_obj['user_id']
        user=User.objects.get(id=user_id)
        review_id=request.POST.getlist('review_id')
        file=request.FILES.getlist('file_choice')
        reason=request.POST.get('reason')
        order_id=request.POST.get('order_id')
        list_id=request.POST.getlist('id')
        file_preview=request.FILES.getlist('file_preview')
        duration=request.POST.getlist('duration')
        list_preview=[None for  i in range(len(file))]
        list_duration=[0 for  i in range(len(file))]
        for i in range(len(list_preview)):
            for j in range(len(file_preview)):
                if i==j:
                    list_preview[i]=file_preview[j]
        for i in range(len(list_duration)):
            for j in range(len(duration)):
                if i==j:
                    list_duration[i]=float(duration[j])
        total_xu=request.POST.get('total_xu')
        shop=shop.objects.get(user=user)
        orderitem_id=request.POST.getlist('orderitem_id')
        orderitem=OrderItem.objects.filter(id__in=orderitem_id)
        review_rating=request.POST.getlist('review_rating')
        review_text=request.POST.getlist('review_text')
        info_more=request.POST.getlist('info_more')
        rating_anonymous=request.POST.getlist('rating_anonymous')
        list_anonymous_review=[False if rating_anonymous[i]=='false' else True for i in range(len(rating_anonymous))]
        rating_bab_category=request.POST.getlist('rating_bab_category')
        if review_id:
            Media_review.objects.filter(review=None).delete()
            reviews=ReView.objects.filter(id__in=review_id)
            list_media=Media_review.objects.bulk_create(
                [Media_review(
                    upload_by=user,
                    file=file[i],
                    file_preview=list_preview[i],
                    duration=list_duration[i]
                )
                for i in range(len(file))
                ]
            )
            list_mediaupload=Media_review.objects.filter(upload_by=user).order_by('-id')[:len(file)]
            for review in reviews:
                for i in range(len(review_id)):
                    if i==list(reviews).index(review):
                        review.media_upload.add(*list_mediaupload)
                        review.review_rating=review_rating[i]
                        review.review_text=review_text[i]
                        review.info_more=info_more[i]
                        review.anonymous_review=list_anonymous_review[i]
                        review.rating_product=int(rating_bab_category[i].split(',')[0])
                        review.rating_seller_service=int(rating_bab_category[i].split(',')[1])
                        review.rating_shipping_service=int(rating_bab_category[i].split(',')[2])
                        review.edited=True
            bulk_update(reviews)
            data={
                'list_review':[{'id':review.id,'review_text':review.review_text,'created':review.created,
                'info_more':review.info_more,'rating_anonymous':review.anonymous_review,'list_file':[{'filetype':file.filetype(),'file':file.upload_file(),
                'media_preview':file.media_preview(),'duration':file.duration,'file_id':file.id,'show':False}
                 for file in review.media_upload.all()],
                'rating_bab_category':[review.rating_product,review.rating_seller_service,review.rating_shipping_service],
                'review_rating':review.review_rating,'edited':review.edited,
                'item_image':review.orderitem.product.item.media_upload.all()[0].upload_file(),'item_url':review.orderitem.product.item.get_absolute_url(),
                'item_name':review.orderitem.product.item.name,'color_value':review.orderitem.product.get_color(),
                'size_value':review.orderitem.product.get_size()
                } for review in reviews]
            }
            return Response(data)
        elif reason:
            order=Order.objects.get(id=order_id)
            order.canceled=True
            order.canceled_date=timezone.now()
            order.save()
            if order.payment_choice=="Paypal":
                sale = Sale.find(order.payment_number)
                refund = sale.refund({
                    "amount": {
                    "total":order.total_final_order(),
                    "currency": "USD"
                    }
                })
            cancel=CancelOrder.objects.create(
                order=order,
                reason=reason,
                user=user
            )
            order_items = order.items.all()
            order_items.update(ordered=False)
            for item in order_items:
                item.save()
                products=Variation.objects.get(orderitem=item)
                products.inventory += item.quantity
                products.save()
                for byproduct in item.byproduct.all():
                    product=Variation.objects.get(byproductcart=byproduct)
                    product.inventory+=byproduct.quantity
                    product.save()
            data={
                'cancel':'cancel'
            }
            return Response(data)
        else:
            shop.xu=total_xu
            shop.save()
            list_media=Media_review.objects.bulk_create(
                [Media_review(
                    upload_by=user,
                    file=file[i],
                    file_preview=list_preview[i],
                    duration=list_duration[i]
                )
                for i in range(len(file))
                ]
            )
            count_media=Media_review.objects.filter(upload_by=user).count()
            list_mediaupload=Media_review.objects.filter(upload_by=user)[count_media-len(file):count_media]
            reviews=[
                ReView(
                    user=user,
                    orderitem=orderitem[i],
                    review_rating=review_rating[i],
                    review_text=review_text[i],
                    info_more=info_more[i],
                    anonymous_review=list_anonymous_review[i],
                    rating_product=int(rating_bab_category[i].split(',')[0]),
                    rating_seller_service=int(rating_bab_category[i].split(',')[1]),
                    rating_shipping_service=int(rating_bab_category[i].split(',')[2]),
                ) for i in range(len(orderitem_id))
            ]
            
            ReView.objects.bulk_create(reviews)
            count_review=ReView.objects.filter(user=user).count()
            from_review=count_review-len(orderitem_id)
            list_reviews=ReView.objects.filter(user=user)[from_review:count_review]
            for review in list_reviews:
                for j in range(len(list_id)):
                    if int(list_id[j])==review.orderitem.id:
                        review.media_upload.add(list_mediaupload[j])
            data={'review':'review'}
            return Response(data)

class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    model = User
    permission_classes = (AllowAny,)
    def get_object(self, queryset=None):
        obj = self.user
        return obj
    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # Check old password
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
            # set_password also hashes the password that the user will get
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            response = {
                'status': 'success',
                'code': status.HTTP_200_OK,
                'message': 'Password updated successfully',
                'data': []
            }

            return Response(response)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

