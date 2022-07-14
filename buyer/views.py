
# Create your views here.
from twilio.rest import Client
from django.db.models import Q
from django.conf import settings
from datetime import timedelta
from django.db.models import F
from django.core.mail import EmailMessage
from rest_framework_simplejwt.backends import TokenBackend
from django.urls import reverse
from channels.generic.websocket import WebsocketConsumer
from django.utils.http import urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes,smart_str, force_str, smart_bytes, DjangoUnicodeDecodeError
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from rest_framework.generics import (
    ListAPIView, RetrieveAPIView,GenericAPIView,
)
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from drf_multiple_model.views import ObjectMultipleModelAPIView
from django.core.paginator import Paginator
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from django.contrib.auth.decorators import login_required
from django.db.models import Max, Min, Count, Avg,Sum
from shop.models import *
from category.models import *
from orders.models import *
from carts.models import *
from discounts.models import *
from chats.models import *
from city.models import *
from myweb.models import *
from account.models import *
from itemdetail.models import *
from orderactions.models import *
from rest_framework.decorators import api_view
from bulk_update.helper import bulk_update
from .serializers import (ChangePasswordSerializer,UserSerializer,SMSPinSerializer,
SMSPinSerializer,SMSVerificationSerializer,CategorySerializer,SetNewPasswordSerializer,
UserprofileSerializer,ShopinfoSerializer,ItemSerializer,
ItemSellerSerializer,ItemrecentlySerializer,ShoporderSerializer,ImagehomeSerializer,
CategoryhomeSerializer,AddressSerializer,OrderSerializer,OrderdetailSerializer,
ReviewSerializer,CartitemcartSerializer,CartviewSerializer,
)
from rest_framework_simplejwt.tokens import AccessToken,OutstandingToken
from oauth2_provider.models import AccessToken, Application
from .send_email import send_register_mail, send_reset_password_email
import random
import string
import json
import datetime,jwt
from django.contrib.auth import authenticate,login,logout
from rest_framework import status,viewsets,generics
from django.contrib.auth.models import User
from rest_framework.exceptions import AuthenticationFailed
import paypalrestsdk
from paypalrestsdk import Sale
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters
sensitive_post_parameters_m = method_decorator(
    sensitive_post_parameters("password1", "password2")
)
paypalrestsdk.configure({
  'mode': 'sandbox', #sandbox or live
  'client_id': 'AY2deOMPkfo32qrQ_fKeXYeJkJlAGPh5N-9pdDFXISyUydAwgRKRPRGhiQF6aBnG68V6czG5JsulM2mX',
  'client_secret': 'EJBIHj3VRi77Xq3DXsQCxyo0qPN7UFB2RHQZ3DOXLmvgNf1fXWC5YkKTmUrIjH-jaKMSYBrH4-9RjiHA' })

account_sid = settings.TWILIO_ACCOUNT_SID
auth_token = settings.TWILIO_AUTH_TOKEN
client = Client(account_sid, auth_token)

def create_ref_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=14))
class UserView(APIView):
    def get(self, request):
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        if not token:
            raise AuthenticationFailed('Unauthenticated!')
        try:
            user=request.user
            Profile.objects.filter(user=user).update(online=True)
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Unauthenticated!')
        user=request.user
        serializer = UserprofileSerializer(user)
        return Response(serializer.data)

class UpdateOnline(APIView):
    permission_classes = (IsAuthenticated,)
    def post(self,request):
        online=request.POST.get('online')
        if online=='false':
            Profile.objects.filter(user=request.user).update(online=False,is_online=timezone.now())
        return Response({'pk':'ki'})

class RegisterView(APIView):
    permission_classes = (AllowAny,)
    serializers_class=UserSerializer
    def post(self, request, *args, **kwargs):
        serializer = self.serializers_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class Registeremail(APIView):
    def post(self,request):
        username=request.POST.get('username')
        email=request.POST.get('email')
        verify=request.POST.get('verify')
        check_user=User.objects.filter(Q(username=username) | Q(email=email))
        if check_user.exists():
            return Response({'error':True})
        else:
            usr_otp = random.randint(100000, 999999)
            Verifyemail.objects.create(email = email, otp = usr_otp)
            email_body = f"Chào mừng bạn đến với anhdai.com,\n Mã xác nhận email của bạn là: {usr_otp}"
            data = {'email_body': email_body, 'to_email':email,
                    'email_subject': "Welcome to AnhDai's Shop - Verify Your Email!"}
            email = EmailMessage(subject=data['email_subject'], body=data['email_body'], to=[data['to_email']])
            email.send()
            return Response({'error':False})
        
class VerifyEmailView(APIView):
    permission_classes = (AllowAny,)
    def post(self, request):
        otp = int(request.POST.get("otp"))
        email=request.POST.get('email')
        reset=request.POST.get('reset')
        verifyemail=Verifyemail.objects.filter(email=email).last()
        if verifyemail.otp==otp:    
            return Response({'verify':True})
        else:
            return Response({'verify':False})

class Sendotp(APIView):
    permission_classes = (AllowAny,)
    def post(self, request, *args, **kwargs):
        phone=request.POST.get('phone')
        login=request.POST.get('login')
        reset=request.POST.get('reset')
        usr_otp = random.randint(100000, 999999)
        otp=SMSVerification.objects.create(pin=usr_otp,phone=phone)
        if login: 
            message = client.messages.create(
                body=f"DE DANG NHAP TAI KHOAN VUI LONG NHAP MA XAC THUC {otp.pin}. Co hieu luc trong 15 phut. Khong chia se ma nay voi nguoi khac",
                from_=settings.TWILIO_FROM_NUMBER,
                to=str(phone)
            )
        elif reset:
            message = client.messages.create(
                body=f"DE CAP NHAT MAT KHAU VUI LONG NHAP MA XAC THUC {otp.pin}. Co hieu luc trong 15 phut. Khong chia se ma nay voi nguoi khac",
                from_=settings.TWILIO_FROM_NUMBER,
                to=str(phone)
            )
        else:
            message = client.messages.create(
                body=f"DE DANG KY TAI KHOAN VUI LONG NHAP MA XAC THUC {otp.pin}. Co hieu luc trong 15 phut. Khong chia se ma nay voi nguoi khac",
                from_=settings.TWILIO_FROM_NUMBER,
                to=str(phone)
            )
        data={'id':otp.id}
        return Response(data)

class VerifySMSView(APIView):
    permission_classes = (AllowAny,)
    def post(self, request):
        id=request.POST.get('id')
        pin = int(request.POST.get("pin"))
        phone=request.POST.get('phone')
        reset=request.POST.get('reset')
        otp=SMSVerification.objects.get(id=id)
        profile=Profile.objects.filter(phone=phone)
        if otp.pin==pin:
            otp.verified=True
            otp.save()
            if profile.exists():
                if reset:
                    user=profile.first().user
                    uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
                    token = default_token_generator.make_token(user)
                    return Response({'verify':True,'token':token,'uidb64':uidb64})
                return Response({'verify':True,'avatar':profile.first().avatar.url,'username':profile.first().user.username,'user_id':profile.first().user.id})
            else:
                return Response({'verify':True})
        else:
            return Response({'verify':False})

class LoginView(APIView):
    permission_classes = (AllowAny,)
    def post(self, request,):
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        token=request.POST.get('token')
        user_id=request.POST.get('user_id')
        if token:
            token = AccessToken.objects.get(token=token)
            user = token.user
        elif user_id:
            user=User.objects.get(id=user_id)
        else:
            if email:
                user = authenticate(request, email=username, password=password)
            else:
                user = authenticate(request, username=username, password=password)
        try:
            refresh = RefreshToken.for_user(user)
            data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'access_expires': datetime.datetime.now()+settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']
            }
            return Response(data)
        except Exception:
            raise AuthenticationFailed('Unauthenticated!')

class LogoutView(APIView):
    def post(self, request):
        response = Response()
        response.delete_cookie('jwt')
        response.data = {
            'message': 'success'
        }
        return response

class HomeAPIView(APIView):
    permission_classes = (AllowAny,)
    def get(self,request):
        list_flashsale=Flash_sale.objects.filter(valid_to__gt=timezone.now(),valid_from__lt=timezone.now())
        list_items=Item.objects.filter(flash_sale__in=list_flashsale).prefetch_related('flash_sale').prefetch_related('media_upload').prefetch_related('variation_item__color').prefetch_related('variation_item__size').prefetch_related('cart_item__order_cartitem').distinct()
        data={
            'a':[{'item_name':i.name,'item_image':i.get_image_cover(),'number_order':i.number_order(),
            'percent_discount':i.discount_flash_sale(),'item_id':i.id,'item_inventory':i.total_inventory(),'max_price':i.max_price(),'item_url':i.get_absolute_url(),
            'min_price':i.min_price(),'quantity_limit_flash_sale':i.quantity_limit_flash_sale} for i in list_items],
            'list_flashsale':list_flashsale.values('valid_from','valid_to')
        }
        return Response(data)

class CategoryListView(ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class=CategoryhomeSerializer
    def get_queryset(self):
        return Category.objects.exclude(image='')

class Listitemseller(ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ItemSellerSerializer
    def get_queryset(self):
        return Item.objects.filter(cart_item__order_cartitem__ordered=True).annotate(count_order= Count('cart_item__order_cartitem')).prefetch_related('cart_item__order_cartitem').prefetch_related('media_upload').prefetch_related('variation_item__color').prefetch_related('variation_item__size').order_by('-count_order')

class ListTrendsearch(ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ItemSellerSerializer
    def get_queryset(self):
        return Item.objects.filter(cart_item__order_cartitem__ordered=True).annotate(count_like= Count('liked')).annotate(count_order= Count('cart_item__order_cartitem')).annotate(count_order= Count('cart_item__order_cartitem')).annotate(count_review= Count('cart_item__review_item')).prefetch_related('media_upload').prefetch_related('cart_item__order_cartitem').prefetch_related('variation_item__color').prefetch_related('variation_item__size').order_by('-count_like','-count_review','-count_order')

def search_matching(list_keys):
    q = Q()
    for key in list_keys:
        q |= Q(name__icontains = key)
    return Item.objects.filter(q).values('name').order_by('category__title').distinct()

def get_count(category):
    return Item.objects.filter(category=category).count()

class DetailAPIView(APIView):
    permission_classes = (AllowAny,)
    def get(self, request,slug):
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        category=Category.objects.filter(slug=slug)
        item=Item.objects.filter(slug=slug)
        shop=Shop.objects.filter(slug=slug)
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
        data={}
        if category.exists():
            category=Category.objects.get(slug=slug)
            category_children=Category.objects.filter(parent=category)
            category_choice=category.get_descendants(include_self=False).filter(choice=True)
            list_items=Item.objects.filter(category__in=category_choice)
            items=Item.objects.filter(category__in=category_choice).prefetch_related('main_product').prefetch_related('shop_program').prefetch_related('promotion_combo').prefetch_related('media_upload').prefetch_related('variation_item__color').prefetch_related('variation_item__size')
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
                items=items.annotate(avg_rating= Avg('cart_item__review_item__review_rating')).filter(avg_rating__gte=rating)
            if maxprice and minprice:
                max_price=int(maxprice)
                min_price=int(minprice)
                items=items.annotate(min=Min('variation_item__price')).filter(min__gte=min_price,min__lte=max_price)
            if sortby:
                items=items.filter(cart_item__order_cartitem__ordered=True)
                if sortby=='pop':
                    items=items.annotate(count_like= Count('liked')).annotate(count_order= Count('cart_item__order_cartitem')).annotate(count_review= Count('cart_item__review_item')).order_by('-count_like','-count_review','-count_order')
                elif sortby=='ctime':
                    items=items.annotate(count_order= Count('cart_item__order_cartitem__id')).annotate(count_review= Count('cart_item__review_item')).order_by('-id')
                elif sort_by=='price':
                    items=items.annotate(avg_price= Avg('variation_item__price')).order_by('avg_price')
                    if order=='desc':
                        items=items.annotate(avg_price= Avg('variation_item__price')).order_by('-avg_price')
            paginator = Paginator(items,30)
            page_obj = paginator.get_page(page)
            shoptype=[{'value':shop.shop_type,'name':shop.get_shop_type_display()} for shop in list_shop ]
            status=[{'value':item.status,'name':item.get_status_display()} for item in list_items]
            data.update({
                'image_home':[{'image':i.image.url,'url':i.url_field} for i in category.image_category.all()],
                'shoptype':list({item['value']:item for item in shoptype}.values()),
                'cities':list(set([shop.city for shop in list_shop if shop.city!=None])),
                'unitdelivery':list(set(['Nhanh','Hỏa tốc'])),
                'brands':list(set([item.brand for item in list_items])),
                'status':list({item['value']:item for item in status}.values()),
                'category_choice':[{'id':i.id,'title':i.title,'count_item':i.item_set.all().count(),'url':i.get_absolute_url()} for i in category_choice if i.item_set.all().count()>0],
                'category_info':{'title':category.title,'image':category.image.url,'id':category.id},
                'category_children':[{'id':i.id,'title':i.title,'url':i.get_absolute_url()} for i in category_children],
                'list_item_page':[{'item_name':i.name,'item_image':i.get_image_cover(),
                'item_url':i.get_absolute_url(),'percent_discount':i.percent_discount(),'min_price':i.min_price(),
                'shop_city':i.shop.city,'item_brand':i.brand,'voucher':i.get_voucher(),
                'review_rating':i.average_review(),'num_like':i.num_like(),'max_price':i.max_price(),
                'promotion':i.get_promotion(),
                'shock_deal':i.shock_deal_type(),'num_order':i.number_order()
                }
            for i in page_obj],'page_count':paginator.num_pages
            })
            return Response(data)

        elif item.exists():
            item=Item.objects.get(slug=slug)
            item.views += 1
            item.save()
            items=Item.objects.filter(shop=item.shop)
            item_detail=Detail_Item.objects.filter(item=item).values()
            vouchers=Voucher.objects.filter(product=item,valid_to__gte=datetime.datetime.now()-datetime.timedelta(seconds=10))
            deal_shock=Buy_with_shock_deal.objects.filter(main_product=item,valid_to__gt=datetime.datetime.now()-datetime.timedelta(seconds=10)).order_by('valid_to')
            list_hot_sales=Item.objects.filter(shop=item.shop,cart_item__order_cartitem__ordered=True).annotate(count=Count('cart_item__order_cartitem__id')).prefetch_related('shop_program').prefetch_related('promotion_combo').prefetch_related('media_upload').prefetch_related('variation_item__color').prefetch_related('variation_item__size').order_by('-count')
            if deal_shock.exists():
                byproduct=deal_shock.first().byproduct.all()
                main_product=item.variation_set.all()[0]
                data.update({'byproduct':[{'item_name':i.name,'item_image':i.get_image_cover(),
                'item_url':i.get_absolute_url(),'percent_discount':i.percent_discount(),'min_price':i.min_price(),
                'max_price':i.max_price(),'discount_deal':i.discount_deal()
                } for i in byproduct]})
            promotion_combo=Promotion_combo.objects.filter(product=item,valid_to__gt=datetime.datetime.now()-datetime.timedelta(seconds=10))
            flash_sale=Flash_sale.objects.filter(product=item,valid_to__gt=datetime.datetime.now()-datetime.timedelta(seconds=10))
            order=Order.objects.filter(items__product__item=item,received=True)
            reviews=ReView.objects.filter(cartitem__product__item=item)
            variation=Variation.objects.filter(item=item)
            data.update({'count_variation':item.count_variation(),'item_detail':item_detail,
            'item_name':item.name,'min_price':item.min_price(),'max_price':item.max_price(),
            'id':item.id,'num_like_item':item.num_like(),'percent_discount':item.percent_discount(),
            'review_rating':item.average_review(),'count_review':item.count_review(),'user_id':item.shop.user.id,
            'category':item.category.get_full_category(),'media_upload':[{'file':i.get_media(),
            'image_preview':i.file_preview(),'duration':i.duration,'media_type':i.media_type(),
            } for i in item.media_upload.all()],'size':item.get_size(),'color':item.get_color(),
            'item_inventory':item.total_inventory(),
            'num_order':item.number_order(),'description':item.description,
            
            'shock_deal_type':item.shock_deal_type(),
            'deal_shock':list(deal_shock.values()),'flash_sale':list(flash_sale.values()),
            'promotion_combo':list(promotion_combo.values()),'user_id':item.shop.user_id,
            'voucher':list(vouchers.values()),
            'list_host_sale':[{'item_name':i.name,'item_image':i.get_image_cover(),'max_price':i.max_price(),
            'percent_discount':i.percent_discount(),'min_price':i.min_price(),
            'item_url':i.get_absolute_url()
            } for i in list_hot_sales]
            })
            
            if token:
                user=request.user
                if ItemViews.objects.filter(item=item,user=user).filter(create_at__gte=datetime.datetime.now().replace(hour=0,minute=0,second=0)).count()==0:
                    ItemViews.objects.create(item=item,user=user)
                like=False
                if user in item.liked.all():
                    like=True
                exist_thread=False
                threads = Thread.objects.filter(participants=user).filter(participants=item.shop.user)
                if threads.exists():
                    data.update({'thread_id':threads.first().id})
                    exist_thread=True
                data.update({'user':user.id,'like':like,'voucher_user':[True if user in voucher.user.all() else False for voucher in vouchers],
                'exist_thread':exist_thread})
            return Response(data)
        elif shop.exists():
            shop=Shop.objects.get(slug=slug)
            shop.views += 1
            shop.save()
            list_voucher=Voucher.objects.filter(shop=shop,valid_to__gt=timezone.now(),valid_from__lte=timezone.now())
            deal_shock=Buy_with_shock_deal.objects.filter(shop=shop,valid_to__gt=timezone.now(),valid_from__lte=timezone.now())
            main_product=Item.objects.filter(main_product__in=deal_shock)
            promotion_combo=Promotion_combo.objects.filter(shop=shop,valid_to__gt=timezone.now(),valid_from__lte=timezone.now())
            item_combo=Item.objects.filter(promotion_combo__in=promotion_combo)
            items=Item.objects.filter(shop=shop).prefetch_related('main_product').prefetch_related('promotion_combo').prefetch_related('shop_program')
            category_children=Category.objects.filter(item__shop=shop).distinct()
            if categoryID:
                category_choice=Category.objects.get(id=categoryID)
                items=items.filter(category=category_choice)
            if rating_score:
                rating=int(rating_score)
                items=items.annotate(avg_rating= Avg('cart_item__review_item__review_rating')).filter(avg_rating__gte=rating)
            if maxprice and minprice:
                max_price=int(maxprice)
                min_price=int(minprice)
                items=items.annotate(min=Min('variation_item__price')).filter(min__gte=min_price,min__lte=max_price)
            if sortby:
                items=items.filter(cart_item__order_cartitem__ordered=True)
                if sortby=='pop':
                    items=items.annotate(count_like= Count('liked')).annotate(count_order= Count('cart_item__order_cartitem')).annotate(count_order= Count('cart_item__order_cartitem')).annotate(count_review= Count('cart_item__review_item')).order_by('-count_like','-count_review','-count_order')
                elif sortby=='ctime':
                    items=items.annotate(count_order= Count('cart_item__order_cartitem__id')).annotate(count_review= Count('cart_item__review_item')).order_by('-id')
                elif sort_by=='price':
                    items=items.annotate(avg_price= Avg('variation_item__price')).order_by('avg_price')
                    if order=='desc':
                        items=items.annotate(avg_price= Avg('variation_item__price')).order_by('-avg_price')
            paginator = Paginator(items,30)
            page_obj = paginator.get_page(page)
            count_follow=Shop.objects.filter(followers=shop.user).count()
            data.update({'avatar':shop.user.profile.avatar.url,'shop_url':shop.get_absolute_url(),'count_followings': count_follow,
                'shop_name':shop.name,'shop':'shop','user_id':shop.user_id,'created':shop.create_at,
                'online':shop.user.profile.online,'num_followers':shop.num_follow(),'slug':shop.slug,
                'is_online':shop.user.profile.is_online,'count_product':shop.count_product(),
                'total_review':shop.total_review(),'averge_review':shop.averge_review(),
                'promotion_combo':[{'combo_type':promotion.combo_type,
                'quantity_to_reduced':promotion.quantity_to_reduced,'limit_order':promotion.quantity_to_reduced,
                'discount_percent':promotion.discount_percent,'discount_price':promotion.discount_price,
                'price_special_sale':promotion.price_special_sale} for promotion in promotion_combo],
                'item_combo':[{'item_name':i.name,'item_image':i.get_image_cover(),
                'item_url':i.get_absolute_url(),'percent_discount':i.percent_discount(),'min_price':i.min_price(),
                'shop_city':i.shop.city,'item_brand':i.brand,'voucher':i.get_voucher(),
                'review_rating':i.average_review(),'num_like':i.num_like(),'max_price':i.max_price()} for i in item_combo],
                'list_item_page':[{'item_name':i.name,'item_image':i.get_image_cover(),
                'item_url':i.get_absolute_url(),'percent_discount':i.percent_discount(),'min_price':i.min_price(),
                'shop_city':i.shop.city,'item_brand':i.brand,'voucher':i.get_voucher(),
                'review_rating':i.average_review(),'num_like':i.num_like(),'max_price':i.max_price(),
                'promotion':i.get_promotion(),
                'shock_deal':i.shock_deal_type(),'num_order':i.number_order()
                }
                for i in page_obj],'page_count':paginator.num_pages,'list_voucher':list_voucher.values(),
                'main_product':[{'item_name':i.name,'item_image':i.get_image_cover(),
                'item_url':i.get_absolute_url(),'percent_discount':i.percent_discount(),'min_price':i.min_price(),
                'shop_city':i.shop.city,'item_brand':i.brand,'voucher':i.get_voucher(),
                'review_rating':i.average_review(),'num_like':i.num_like(),'max_price':i.max_price()} for i in main_product],
                'total_order':shop.total_order(),'list_category_child':[{'title':category.title,'id':category.id,'url':category.get_absolute_url()} for category in category_children]})
            
            if token:
                user=request.user
                if ShopViews.objects.filter(shop=shop,user=user).filter(create_at__gte=datetime.datetime.now().replace(hour=0,minute=0,second=0)).count()==0:
                    ShopViews.objects.create(shop=shop,user=user)
                follow=False
                if user in shop.followers.all():
                    follow=True
                exist_thread=False
                threads = Thread.objects.filter(participants=user).filter(participants=shop.user)
                if threads.exists():
                    data.update({'thread_id':threads.first().id})
                    exist_thread=True
                data.update({'follow':follow,'user':user.id})
                
            return Response(data)
           
    def post(self, request, *args, **kwargs):
        shop_name=request.POST.get('shop_name')
        shop=Shop.objects.get(name=shop_name)
        user=request.user
        follow=False
        count_follow=Shop.objects.filter(followers=shop.user).count()
        if user in shop.followers.all():
            follow=False
            shop.followers.remove(user)
        else:
            follow=True
            shop.followers.add(user)
        data={'num_followers':shop.num_follow(),'follow':follow,'online':shop.user.profile.online,
        'num_followers':shop.num_follow(),'count_followings': count_follow,
        'is_online':shop.user.profile.is_online,'count_product':shop.count_product(),
        'total_review':shop.total_review(),'averge_review':shop.averge_review()}
        return Response(data)

class Topsearch(APIView):
    def get(self,request):
        from_item=0
        to_item=5
        from_item=request.GET.get('from_item')
        to_item=request.GET.get('to_item')
        keyword=list(SearchKey.objects.all().order_by('-total_searches').values('keyword').filter(updated_on__gte=datetime.datetime.now()-datetime.timedelta(days=7)))
        list_keys=[i['keyword'] for i in keyword]
        items=search_matching(list_keys)
        list_title_item=[i['name'] for i in items]
        result_item = dict((i, list_title_item.count(i)) for i in list_title_item)
        list_sort_item={k: v for k, v in sorted(result_item.items(), key=lambda item: item[1],reverse=True)}
        list_name_top_search=sorted(list_sort_item, key=list_sort_item.get, reverse=True)[:20]
        item_top_search=Item.objects.filter(Q(name__in=list_name_top_search)).prefetch_related('media_upload').select_related('category').prefetch_related('cart_item__order_cartitem')
        data={
        'item_top_search':[{'image':item.get_image_cover(),'title':item.category.title,'count':get_count(item.category),'name':item.name,'number_order':item.number_order()} for item in item_top_search]}
        return Response(data)

class SearchitemAPIView(APIView):
    permission_classes = (AllowAny,)
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
            list_items = Item.objects.filter(Q(name__icontains=keyword)|Q(shop__name=keyword) | Q(brand__in=keyword)|Q(category__title__in=keyword)).order_by('name').distinct()
            items = Item.objects.filter(Q(name__icontains=keyword) | Q(
            brand__in=keyword)|Q(category__title__in=keyword)).prefetch_related('media_upload').prefetch_related('main_product').prefetch_related('promotion_combo').prefetch_related('shop_program').prefetch_related('variation_item__color').prefetch_related('variation_item__size').prefetch_related('cart_item__order_cartitem').distinct()
            category_choice=Category.objects.filter(item__in=list_items).order_by('name').distinct()
            list_shop=Shop.objects.filter(item__in=list_items)
            SearchKey.objects.get_or_create(keyword=keyword)
            SearchKey.objects.filter(keyword=keyword).update(total_searches=F('total_searches') + 1)
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
            items=items.annotate(avg_rating= Avg('cart_item__review_item__review_rating')).filter(avg_rating__gte=rating)
        if sortby:
            if sortby=='pop':
                items=items.annotate(count_like= Count('liked')).annotate(count_order= Count('cart_item__order_cartitem')).annotate(count_order= Count('cart_item__order_cartitem')).annotate(count_review= Count('cart_item__review_item')).order_by('-count_like','-count_review','-count_order')
            elif sortby=='ctime':
                items=items.annotate(count_order= Count('cart_item__order_cartitem__id')).annotate(count_review= Count('cart_item__review_item')).order_by('-id')
            elif sortby=='price':
                items=items.annotate(avg_price= Avg('variation_item__price')).order_by('avg_price')
                if order=='desc':
                    items=items.annotate(avg_price= Avg('variation_item__price')).order_by('-avg_price')
        paginator = Paginator(items,30)
        page_obj = paginator.get_page(page)
        shoptype=[{'value':shop.shop_type,'name':shop.get_shop_type_display()} for shop in list_shop]
        status=[{'value':item.status,'name':item.get_status_display()} for item in list_items]
        data={
            'shoptype':list({item['value']:item for item in shoptype}.values()),
            'cities':list(set([shop.city for shop in list_shop if shop.city!=None])),
            'unitdelivery':list(set(['Nhanh','Hỏa tốc'])),
            'brands':list(set([item.brand for item in list_items])),
            'status':list({item['value']:item for item in status}.values()),
            'category_choice':[{'id':i.id,'title':i.title,'count_item':i.item_set.all().count(),'url':i.get_absolute_url()} for i in category_choice],
            'list_item_page':[{'item_name':i.name,'item_image':i.get_image_cover(),
            'item_url':i.get_absolute_url(),'percent_discount':i.percent_discount(),'min_price':i.min_price(),
            'shop_city':i.shop.city,'item_brand':i.brand,'voucher':i.get_voucher(),
            'review_rating':i.average_review(),'num_like':i.num_like(),'max_price':i.max_price(),
            'promotion':i.get_promotion(),
            'shock_deal':i.shock_deal_type(),'num_order':i.number_order()
            }
        for i in page_obj],'page_count':paginator.num_pages
        }
        return Response(data)
        
class ImageHomeAPIView(ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ImagehomeSerializer
    def get_queryset(self):
        return Image_home.objects.all()

class ProductInfoAPIVIew(APIView):
    permission_classes = (AllowAny,)
    def get(self,request,id):
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
        item=Item.objects.get(id=id)
        if shop_id:
            shop=Shop.objects.get(id=id)
            serializer = ShopinfoSerializer(shop,context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        elif review:
            list_review=ReView.objects.filter(cartitem__product__item=item)
            reviews=list_review
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
                'info_more':review.info_more,'anonymous_review':review.anonymous_review,
                'review_rating':review.review_rating,'num_like':review.num_like(),'user_like':[user.id for user in review.like.all()],
                'list_file':[{'file_id':file.id,'filetype':file.filetype(),'file':file.file.url,
                'media_preview':file.get_media_preview(),'duration':file.duration,'show':False}
                for file in review.media_review.all()],'color_value':review.cartitem.product.get_color(),
                'size_value':review.cartitem.product.get_size(),
                'item_name':review.cartitem.item.name,
                'user':review.user.username,'shop':review.shop_name(),
                'url_shop':review.user.shop.get_absolute_url(),
                } for review in page_obj],'page_count':paginator.num_pages,
                'rating':[review.review_rating for review in list_review],'has_comment':count_comment,
                'has_media':count_media
                }
            return Response(data)

    def post(self, request, *args, **kwargs):
        item_id=request.POST.get('item_id')
        review_id=request.POST.get('review_id')
        reason=request.POST.get('reason')
        user=request.user
        like_item=True
        like_review=False
        data={}
        if review_id:
            review=ReView.objects.get(id=review_id)
            if reason:
                if Report.objects.filter(user=user,review=review).exists():
                    Report.objects.filter(user=user,review=review).update(reson=reason)
                else:
                    Report.objects.create(user=user,reson=reason,review=review)
                data.update({'report':True})
            else:
                if user in review.like.all():
                    like_review=False
                    review.like.remove(user)  
                else:
                    review.like.add(user)  
            data.update({'like_review':like_review,'num_like_review':review.num_like()})  
        if item_id:
            item=Item.objects.get(id=item_id)
            if user in item.liked.all():
                item.liked.remove(user)
                like_item=False
            else:
                item.liked.add(user) 
            data.update({'num_like_item':item.num_like(),'like_item':like_item})  
        return Response(data)

class ShopinfoAPIVIew(APIView):
    permission_classes = (AllowAny,)
    def get(self,request):
        item_id=request.GET.get('item_id')
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
            items=Item.objects.filter(shop=shop).prefetch_related('media_upload').prefetch_related('main_product').prefetch_related('promotion_combo').prefetch_related('shop_program').prefetch_related('variation_item__color').prefetch_related('variation_item__size').prefetch_related('cart_item__order_cartitem')
            paginator = Paginator(items,30)  # Show 25 contacts per page.
            page_obj = paginator.get_page(1)
            if page:
                page_obj = paginator.get_page(page)
            list_page_item=[{'item_name':i.name,'item_image':i.get_image_cover(),
            'item_url':i.get_absolute_url(),'percent_discount':i.percent_discount(),'min_price':i.min_price(),
            'shop_city':i.shop.city,'item_brand':i.brand,'voucher':i.get_voucher(),
            'review_rating':i.average_review(),'num_like':i.num_like(),'max_price':i.max_price(),
            'promotion':i.get_promotion(),
            'shock_deal':i.shock_deal_type(),'num_order':i.number_order()
            }
            for i in page_obj]
            data={
                'a':list_page_item,'page_count':paginator.num_pages
            }
            return Response(data)

class ListItemRecommendAPIView(APIView):
    permission_classes = (AllowAny,)
    def get(self,request):
        items_recommend=Item.objects.all()
        page_number = request.GET.get('page')
        paginator = Paginator(items_recommend, 30)
        page_obj = paginator.get_page(page_number)
        serializer = ItemSerializer(page_obj,many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
        
class Itemrecently(ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ItemrecentlySerializer
    def get_queryset(self):
        request=self.request
        user=request.user
        return ItemViews.objects.filter(user=user).order_by('-id,item')[:12].distinct()

class Listitemhostsale(ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ItemrecentlySerializer
    def get_queryset(self):
        request=self.request
        shop_id=request.GET.get('shop_id')
        item=Item.objects.filter(shop_id=shop_id).filter(cart_item__order_cartitem__ordered=True).annotate(count_order= Count('cart_item__order_cartitem')).prefetch_related('media_upload').prefetch_related('main_product').prefetch_related('promotion_combo').prefetch_related('shop_program').prefetch_related('variation_item__color').prefetch_related('variation_item__size').prefetch_related('cart_item__order_cartitem').order_by('-count_order')
        return ItemViews.objects.filter(user=user).order_by('-id,item')[:12].distinct()
    
@api_view(['GET', 'POST'])
def save_voucher(request):
    if request.method=="POST":
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        if token:
            user=request.user
            voucher_id=request.POST.get('voucher_id')
            voucher=Voucher.objects.get(id=voucher_id)
            voucher.user.add(user)
            data={'ok':'ok'}
            return Response(data)

@api_view(['GET', 'POST'])
def update_image(request):
    if request.method=="POST":
        file=request.FILES.getlist('file')
        Image_category.objects.bulk_create(
            [Image_category(
                image=i,
                url_field='http://localhost:8000/kids-babies-fashion-cat'
            ) for i in file]
        )
        return Response({'ok':'ok'})

class Category_home(ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = CategorySerializer
    def get_queryset(self):
        return Category.objects.exclude(image=None).order_by('title').values('title').distinct()[:8]
    
class CartAPIView(APIView):
    permission_classes = (AllowAny,)
    def get(self,request):
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        if token:
            list_cart_items=CartItem.objects.filter(ordered=False,user=request.user).select_related('item').select_related('product').prefetch_related('item__main_product').prefetch_related('item__promotion_combo')
            list_cart_item=list_cart_items[0:5]
            count=list_cart_items.count()
            list_cart_item=[{'item_id':cart_item.item_id,'item_name':cart_item.item.name,'id':cart_item.id,
            'item_image':cart_item.get_image(),
            'item_url':cart_item.item.get_absolute_url(),
            'price':cart_item.product.price-cart_item.product.total_discount(),
            'shock_deal_type':cart_item.item.shock_deal_type(),
            'promotion':cart_item.item.get_promotion(),
            } for cart_item in list_cart_item]
            data={
                    'count':count,
                    'a':list_cart_item
                    }
            return Response(data)
        else:
            data={'error':'error'}
            return Response(data)

class UpdateCartAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request):
        item_id=request.GET.get('item_id')
        page = request.GET.get('page')
        item=Item.objects.get(id=item_id)
        items=Item.objects.filter(category=item.category).prefetch_related('media_upload').prefetch_related('main_product').prefetch_related('promotion_combo').prefetch_related('shop_program').prefetch_related('variation_item__color').prefetch_related('variation_item__size').prefetch_related('cart_item__order_cartitem')
        page_no=1
        paginator = Paginator(items,5)  # Show 25 contacts per page.
        page_obj = paginator.get_page(1)
        if page:
            page_obj = paginator.get_page(page)
            page_no=page
        data={
            'page_count':paginator.num_pages,'page':int(page_no),
            'list_item':[{'item_id':i.id,'item_name':i.name,
            'item_image':i.get_image_cover(),
            'percent_discount':i.percent_discount(),'min_price':i.min_price(),
            'shop_city':i.shop.city,'item_brand':i.brand,'voucher':i.get_voucher(),
            'review_rating':i.average_review(),'num_like':i.num_like(),'max_price':i.max_price(),
            'promotion':i.get_promotion(),
            'shock_deal':i.shock_deal_type(),'num_order':i.number_order(),
            'item_url':i.get_absolute_url(),
            }
            for i in page_obj]
        }
        return Response(data)
    def post(self, request,price=0,total=0,count_cartitem=0,total_discount=0,discount_deal=0,discount_voucher=0,discount_promotion=0,count=0,*args, **kwargs):  
        user=request.user
        item_id=request.POST.get('item_id')
        cartitem_id=request.POST.get('cartitem_id')
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
        if cartitem_id:
            cart_item=CartItem.objects.get(id=cartitem_id)
            cart_item.product=product
            cart_item.save()
            data.update({'item':{
            'price':cart_item.product.price,
            'color_value':cart_item.product.get_color(),'size_value':cart_item.product.get_size(),
            'total_price':cart_item.total_discount_cartitem(),'inventory':cart_item.product.inventory,
            }})
        if byproduct_id:
            byproduct=Byproductcart.objects.get(id=byproduct_id)
            byproduct.byproduct=product
            byproduct.save()
            data.update({'item':{
            'price':byproduct.byproduct.price,
            'total_price':byproduct.total_price(),
            'inventory':byproduct.byproduct.inventory,
            'color_value':byproduct.byproduct.get_color(),'size_value':byproduct.byproduct.get_size()
            }})
        order_check = Order.objects.filter(user=user, ordered=False).exclude(items=None)
        for order in order_check:
            discount_voucher+=order.discount_voucher()
            count_cartitem+=order.count_item_cart()
            for cartitem in order.items.all():
                count+=cartitem.count_item_cart()
                total+=cartitem.total_price_cartitem()
                total_discount+=cartitem.discount()
                discount_deal+=cartitem.discount_deal()
                discount_promotion+=cartitem.discount_promotion()  
        data.update({'orders':{
            'total':total,'total_discount':total_discount,'discount_promotion':discount_promotion,
            'discount_deal':discount_deal,'discount_voucher':discount_voucher,'count':count,'count_cartitem':count_cartitem
        }})
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
        
        data={'product_id':product.id,'color_value':product.get_color(),'size_value':product.get_size(),
            'price':product.price,'discount_price':product.total_discount(),'inventory':product.inventory,
            }
        if byproduct_id:
            data.update({'byproduct_id':byproduct_id})
        return Response(data)
    def post(self, request, *args, **kwargs):
        user=request.user
        product_id_choice=request.POST.get('product_id_chocie')
        quantity_product=request.POST.get('quantity_product')
        item_id=request.POST.get('item_id')
        deal_id=request.POST.get('deal_id')
        product_id=request.POST.getlist('product_id')
        byproduct_id_delete=request.POST.getlist('byproduct_id_delete')
        Byproductcart.objects.filter(id__in=byproduct_id_delete).delete()
        list_quantity=request.POST.getlist('quantity')
        quantity_byproduct=request.POST.getlist('quantity_byproduct')
        byproduct_id=request.POST.getlist('byproduct_id')
        cartitem_id=request.POST.get('cartitem_id')
        variation_choice=Variation.objects.get(id=product_id_choice)
        list_variation=Variation.objects.filter(id__in=product_id)
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
            Byproductcart(user=user,item_id=item_id,byproduct=list_variation[i],quantity=int(list_quantity[i]))
            for i in range(len(product_id))]
        )
        byproducts=Byproductcart.objects.order_by('-id')[:len(product_id)]
        cartitem=CartItem.objects.filter(id=cartitem_id)
        if cartitem.exists():
            cartitem_last=cartitem.last()
            cartitem_last.byproduct.add(*byproducts)
            cartitem_last.deal_shock=deal_shock
            cartitem_last.quantity=int(quantity_product)
            if cartitem_last.product!=variation_choice:
                cartitem_last.product=variation_choice
            cartitem_last.save()
            data={'o':'o'}
            return Response(data)
        else:
            cartitem=CartItem.objects.create(
                product=variation_choice,
                user=user,
                ordered=False,
                shop=item.shop,
                deal_shock=deal_shock,
                quantity=int(quantity_product)
                )
            cartitem.byproduct.add(*byproducts)
            data={'o':'o'}
            return Response(data)

class AddToCartAPIView(APIView):
    def get(self,request):
        item_id=request.GET.get('item_id')
        color_id=request.GET.get('color_id')
        size_id=request.GET.get('size_id')
        product=Variation.objects.all()
        if item_id and color_id and size_id:
            product=Variation.objects.get(item_id=item_id,color_id=color_id,size_id=size_id)
        elif item_id and color_id and not size_id:
            product=Variation.objects.get(item_id=item_id,color_id=color_id)
        elif item_id and not color_id and size_id:
            product=Variation.objects.get(item_id=item_id,size_id=size_id)
        elif item_id and not size_id and not color_id:
            product=Variation.objects.get(item_id=item_id)
        data={
            'price':product.price,
            'percent_discout':product.percent_discount,
            'inventory':product.inventory,'id':product.id
            }
        return Response(data)

    def post(self, request, *args, **kwargs):
        user=request.user
        id=request.POST.get('id')
        item_id=request.POST.get('item_id')
        quantity=request.POST.get('quantity')
        item=Item.objects.get(id=item_id)
        if id:
            product=Variation.objects.get(id=id)
        else:
            product=Variation.objects.get(item_id=item_id)
        try:
            cart_item=CartItem.objects.get(
                product=product,
                user=user,
                ordered=False,
                shop=item.shop,
            )
            cart_item.quantity =cart_item.quantity+int(quantity)
            cart_item.save()
            if cart_item.quantity>cart_item.product.inventory:
                cart_item.quantity-=int(quantity)
                cart_item.save()
                return Response({'erorr':'over quantity'})
            else:
                serializer = CartviewSerializer(cart_item,context={"request": request})
                return Response(serializer.data, status=status.HTTP_200_OK)
                
        except Exception:
            cart_item=CartItem.objects.create(
                product=product,
                item_id=item_id,
                user=user,
                ordered=False,
                quantity=int(quantity),
                shop=item.shop,
                )
            serializer = CartviewSerializer(cart_item,context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)
class ShoporderAPI(APIView):
    def get(self,request):
        list_cart_item=CartItem.objects.filter(user=request.user,ordered=False)
        shops=Shop.objects.filter(shop_order__in=list_cart_item).distinct()
        serializer = ShoporderSerializer(shops,many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class CartItemAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request):
        list_cart_item=CartItem.objects.filter(user=request.user,ordered=False).select_related('shop').prefetch_related('item__media_upload').prefetch_related('item__shop_program').prefetch_related('item__main_product').prefetch_related('item__promotion_combo').select_related('product').select_related('product__size').select_related('product__color').prefetch_related('byproduct')
        serializer = CartitemcartSerializer(list_cart_item,many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    def post(self, request,count_cartitem=0,price=0,total=0,total_discount=0,discount_deal=0,discount_voucher=0,discount_promotion=0,count=0, *args, **kwargs):
        user=request.user
        byproduct_id_delete=request.POST.get('byproduct_id_delete')
        byproduct_id=request.POST.get('byproduct_id')
        cartitem_id=request.POST.get('cartitem_id')
        cartitem_id_delete=request.POST.get('cartitem_id_delete')
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
        CartItem.objects.filter(id__in=id_checked).update(check=True)
        CartItem.objects.filter(id__in=id_check).update(check=False)
        ordered_date = timezone.now()
        discount_voucher_shop=0
        if shop_name:
            if order_qs.exists():
                for order in order_qs:
                    if voucher_id:
                        voucher=Voucher.objects.get(id=voucher_id)
                        if voucher.shop.name==order.shop.name:
                            order.voucher=voucher
                            discount_voucher_shop=order.discount_voucher()
                            order.save()
                    if voucher_id_remove:
                        voucher=Voucher.objects.get(id=voucher_id_remove)
                        if voucher.shop.name==order.shop.name:
                            order.voucher=None
                            order.save()
                    list_shop_order.append(order.shop.name)
                    list_cart_item_remove=CartItem.objects.filter(shop=order.shop,id__in=id_check)
                    order.items.remove(*list_cart_item_remove)
                    list_cart_item_add=CartItem.objects.filter(shop=order.shop,id__in=id_checked)
                    order.items.add(*list_cart_item_add) 
                list_shop_remainder=list(set(list_shop) - set(list_shop_order))
                if len(list_shop_remainder)>0:
                    list_shop_remain=Shop.objects.filter(name__in=list_shop_remainder)
                    order = Order.objects.bulk_create([
                    Order(
                        user=user, ordered_date=ordered_date,shop=shop) for shop in list_shop_remain]
                        )
                    orders=Order.objects.filter(user=user)[:len(list_shop_remain)]
                    for order in orders:
                        list_cart_item=CartItem.objects.filter(shop=order.shop,id__in=id_checked)
                        order.items.add(*list_cart_item)
            else:    
                order = Order.objects.bulk_create([
                    Order(
                    user=user, ordered_date=ordered_date,shop=shop) for shop in shops]
                )
                order_s=Order.objects.filter(ordered=False,user=user)
                for order in order_s:
                    list_cart_item=CartItem.objects.filter(shop=order.shop,id__in=id_checked)
                    order.items.add(*list_cart_item)
        else:
            if byproduct_id_delete:
                Byproductcart.objects.get(id=byproduct_id_delete).delete()
            elif byproduct_id :
                byproduct=Byproductcart.objects.get(id=byproduct_id)
                byproduct.quantity=int(quantity)
                byproduct.save()
                price=byproduct.total_price()
            elif cartitem_id:
                cartitem=CartItem.objects.get(id=cartitem_id)
                cartitem.quantity=int(quantity)
                cartitem.save()
                price=cartitem.total_discount_cartitem()
            else:
                CartItem.objects.get(id=cartitem_id_delete).delete()
                Byproductcart.objects.filter(cartitem=None).delete()
        order_check = Order.objects.filter(user=user, ordered=False).exclude(items=None).select_related('voucher').prefetch_related('items__item__media_upload').prefetch_related('items__byproduct').prefetch_related('items__item__main_product').prefetch_related('items__item__promotion_combo').prefetch_related('items__item__shop_program').prefetch_related('items__product__size').prefetch_related('items__product__color')
        for order in order_check:
            discount_voucher+=order.discount_voucher()
            count_cartitem+=order.count_cartitem()
            for cartitem in order.items.all():
                count+=cartitem.count_item_cart()
                total+=cartitem.total_price_cartitem()
                total_discount+=cartitem.discount()
                discount_deal+=cartitem.discount_deal()
                discount_promotion+=cartitem.discount_promotion()
        data={
            'discount_voucher_shop':discount_voucher_shop,
            'price':price,'count':count,'total':total,'discount_deal':discount_deal,
            'total_discount':total_discount,'count_cartitem':count_cartitem,
            'discount_promotion':discount_promotion,'discount_voucher':discount_voucher
            }
        return Response(data)

class ListorderAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request):
        user=request.user
        order_check = Order.objects.filter(user=user, ordered=False).select_related('shop').select_related('voucher').prefetch_related('items__byproduct').prefetch_related('items__item__main_product').prefetch_related('items__item__promotion_combo').prefetch_related('items__item__shop_program').prefetch_related('items__product').exclude(items=None)
        data={
        'orders':[{'discount_voucher_shop':order.discount_voucher(),'total':order.total_price_order(),
            'discount_deal':order.discount_deal(),'count':order.count_item_cart(),
            'count_cartitem':order.count_cartitem(),'shop_name':order.shop.name,
            'discount_promotion':order.discount_promotion(),'total_discount':order.discount(),
            'voucher':order.get_voucher()} 
            for order in order_check]
        }
        return Response(data,status=status.HTTP_200_OK)

@api_view(['GET', 'POST'])
def get_city(request):
    list_city=City.objects.all()
    return Response(list_city.values())

class AddressAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = AddressSerializer
    def get(self,request):
        user=request.user
        default=request.GET.get('default')
        addresses = Address.objects.filter(user=user)
        if default:
            addresses=addresses.filter(default=True)
        serializer = AddressSerializer(addresses,many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        user=request.user
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

class ActionReviewAPI(APIView):
    def get(self,request,id):
        review=Review.objects.get(id=id)
        serializer = ReviewSerializer(review,context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    def post(self,request,id):
        file=request.FILES.getlist('file_choice')
        file_update=request.FILES.getlist('file_update')
        file_id=request.POST.getlist('file_id')
        file_preview=request.FILES.getlist('file_preview')
        file_preview_update=request.FILES.getlist('file_preview_update')
        duration=request.POST.getlist('duration')
        duration_update=request.POST.getlist('duration_update')
        review_rating=request.POST.get('review_rating')
        review_text=request.POST.get('review_text')
        info_more=request.POST.get('info_more')
        anonymous_review=request.POST.get('anonymous_review')
        rating_bab_category=request.POST.getlist('rating_bab_category')
        reason=request.POST.get('reason')
        action=request.POST.get('action')
        data={}
        if action=='update':
            for i in range(len(list_preview)):
                for j in range(len(file_preview)):
                    if i==j:
                        list_preview[i]=file_preview[j]
            for i in range(len(list_preview_update)):
                for j in range(len(file_preview_update)):
                    if i==j:
                        list_preview_update[i]=file_preview_update[j]
        
            review.review_rating=review_rating
            review.review_text=review_text
            review.info_more=info_more
            if anonymous_review=='true':
                review.anonymous_review=True
            else:
                review.anonymous_review=False
            review.rating_product=int(rating_bab_category.split(',')[0])
            review.rating_seller_service=int(rating_bab_category.split(',')[1])
            review.rating_shipping_service=int(rating_bab_category.split(',')[2])
            review.edited=True
            review.save()
            list_mediaupload=Media_review.objects.filter(review_id=id)
            list_mediaupload.exclude(id__in=file_id).delete()
            list_mediaupload_update=list_mediaupload.filter(id__in=file_id)
            for file in list_mediaupload_update:
                for i in range(len(file_update)):
                    if i==list(list_mediaupload_update).index(file):
                        if file_update[i]:
                            file.file=file_update[i]
                        if list_freview_update[i]:
                            file_preview=list_preview_update[i]
                        duration=float(duration_update[i])
            bulk_update(list_mediaupload_update)
            list_media=Media_review.objects.bulk_create(
                [Media_review(
                    upload_by=user,
                    file=file[i],
                    review_id=id,
                    file_preview=list_preview[i],
                    duration=float(duration[i])
                )
                for i in range(len(file))
                ]
            )
            serializer = ReviewSerializer(review,context={"request": request})
            data=serializer.data
        elif action=='report':
            if Report.objects.filter(user=user,review=review).exists():
                Report.objects.filter(user=user,review=review).update(reson=reason)
            else:
                Report.objects.create(user=user,reson=reason,review=review)
            data.update({'report':True})
        else:
            like_review=True
            if user in review.like.all():
                like_review=False
                review.like.remove(user)  
            else:
                review.like.add(user)  
            data.update({'like_review':like_review,'num_like_review':review.num_like()}) 
        return Response(data) 

class CheckoutAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request):
        user=request.user
        orders = Order.objects.filter(user=user, ordered=False).select_related('shop').select_related('voucher').prefetch_related('items__byproduct').prefetch_related('items__item__media_upload').prefetch_related('items__item__main_product').prefetch_related('items__item__promotion_combo').prefetch_related('items__item__shop_program').prefetch_related('items__product__size').prefetch_related('items__product__color').exclude(items=None)
        serializer = OrderSerializer(orders,many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        user=request.user
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
                order.ordered_date=datetime.datetime.now()
                order.accepted_date=datetime.datetime.now()+timedelta(minutes=30)
                order.payment_choice=payment_option
                items = order.items.all()
                items.update(ordered=True) 
                for item in items:
                    item.save()   
                    products=Variation.objects.get(id=item.product_id)
                    products.inventory -= item.quantity
                    products.save()
                    for byproduct in item.byproduct.all():
                        product=Variation.objects.get(id=byproduct.byproduct_id)
                        product.inventory -= byproduct.quantity
                        product.save()
                email_body = f"Hello {user.username}, \n {order.shop.user.username} cảm ơn bạn đã đặt hàng"
                data = {'email_body': email_body, 'to_email': user.email,
                    'email_subject': 'Thanks order!'}
                email = EmailMessage(
                subject=data['email_subject'], body=data['email_body'], to=[data['to_email']])
                email.send()
                
            bulk_update(orders)

            data={'a':'a'}
            return Response(data)

class OrderinfoAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request,id):
        user=request.user
        order=Order.objects.get(id=id)
        serializer = OrderdetailSerializer(order,context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
        
@api_view(['GET', 'POST'])
def payment_complete(request): 
    user=request.user
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
                products=Variation.objects.get(id=item.product_id)
                products.inventory -= item.quantity
                products.save()
                for byproduct in item.byproduct.all():
                    product=Variation.objects.get(id=byproduct.byproduct_id)
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
    permission_classes = (IsAuthenticated,)
    def get(self,request,id):
        user=request.user
        variation=Variation.objects.get(id=id)
        quantity=1
        cartitem_id=0
        cart_item=[]
        list_product=[]
        variation_info={'product_id':variation.id,'color_value':variation.get_color(),'size_value':variation.get_size(),
            'quantity':quantity,'item_id':variation.item_id,'item_name':variation.item.name,'check':True,'main':True,
            'price':variation.price,'discount_price':variation.total_discount(),'item_url':variation.item.get_absolute_url(),
            'size':variation.item.get_size(),'inventory':variation.inventory,'show':False,
            'item_image':variation.item.media_upload.all()[0].get_media(),
            'color':variation.item.get_color()}
        list_product.append(variation_info)
        cartitem=CartItem.objects.filter(product=variation,ordered=False,user=user)
        if cartitem.exists():
            cartitem_last=cartitem.last()
            quantity=cartitem_last.quantity
            cartitem_id=cartitem_last.id
            for byproduct in cartitem_last.byproduct.all():
                cart_item.append({'product_id':byproduct.byproduct_id,'color_value':byproduct.byproduct.get_color(),
                'quantity':byproduct.quantity,'size_value':byproduct.byproduct.get_size(),'item_id':byproduct.item_id,
                'item_name':byproduct.item.name,
                'discount_price':byproduct.byproduct.total_discount(),'byproduct_id':byproduct.id})
        item=Item.objects.get(id=variation.item_id)
        shock_deal=Buy_with_shock_deal.objects.get(main_product=item,valid_to__gt=datetime.datetime.now()-datetime.timedelta(seconds=10))
        byproducts=shock_deal.byproduct.all()
        for item in byproducts:
            if item.get_deal():
                list_product.append({
                    'item_id':item.id,'item_name':item.name,'size':item.get_size_deal(),
                    'color':item.get_color_deal(),'get_deal':item.get_deal(),
                    'color_value':'','quantity':1,'size_value':'',
                    'price':item.max_price(),'show':False,
                    'item_image':item.media_upload.all()[0].get_media(),
                    'check':False,'main':False,'item_url':item.get_absolute_url(),
                    })
        
        for i in range(len(list_product)):
            for j in range(len(cart_item)):
                if list_product[i]['item_id']==cart_item[j]['item_id'] and list_product[i]['main']==False:
                    list_product[i]['product_id']=cart_item[j]['product_id']
                    list_product[i]['color_value']=cart_item[j]['color_value']
                    list_product[i]['size_value']=cart_item[j]['size_value']
                    list_product[i]['quantity']=cart_item[j]['quantity']
                    list_product[i]['discount_price']=cart_item[j]['discount_price']
                    list_product[i]['check']=True
                    list_product[i]['byproduct_id']=cart_item[j]['byproduct_id']
        
        data={
            'cartitem_id':cartitem_id,'deal_id':shock_deal.id,
            'list_product':list_product
        }
        return Response(data)

class PromotionAPIView(APIView):
    permission_classes = (IsAuthenticated,)
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
            'item_id':item.id,'item_name':item.name,
            'item_image':item.media_upload.all()[0].get_media(),
            'item_url':item.get_absolute_url(),'max_price':item.max_price(),
            'min_price':item.min_price(),
            'size':item.get_size(),'color':item.get_color(),'inventory':item.total_inventory()} for item in items]
        }
        return Response(data)

@api_view(['GET', 'POST'])
def upload_file(request):
    user=request.user
    if request.method=="POST":
        file_id=request.POST.get('file_id')
        file=request.FILES.getlist('file')
        file_preview=request.FILES.getlist('file_preview')
        duration=request.POST.getlist('duration')
        name=request.POST.getlist('name')
        media_preview=[None for  i in range(len(file))]
        if file_preview:
            media_preview=file_preview
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
            duration=duration[i],
            upload_by=user)
            for i in range(len(file))])
            
            data={
               'list_file':[{'id':upload_file.id,'file':upload_file.file.url,'file_name':upload_file.file_name,
               'file_preview':upload_file.file_preview(),'filetype':upload_file.filetype(),'duration':upload_file.duration
               } for upload_file in upload_files] 
            }
            return Response(data)

class ProfileAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request):
        user=request.user
        shop_name=None
        count_product=0
        if Shop.objects.filter(user=user).exists():
            shop_name=Shop.objects.filter(user=user).first().name
            count_product=Shop.objects.filter(user=user).first().count_product()
        data={
            'username':user.username,'name':user.shop.name,'email':user.email,
            'phone':str(user.profile.phone),'date_of_birth':user.profile.date_of_birth,
            'image':user.profile.avatar.url,'shop_name':shop_name,
            'gender':user.profile.gender,'user_id':user.id,'count_product':count_product,
            }
        return Response(data)
    def post(self,request):
        shop_name=request.POST.get('shop_name')
        avatar=request.FILES.get('file')
        username=request.POST.get('username')
        gender=request.POST.get('gender')
        name=request.POST.get('name')
        email=request.POST.get('email')
        phone=request.POST.get('phone')
        date_of_birth=request.POST.get('date_of_birth')
        user=request.user
        profile=Profile.objects.get(user=user)
        shop=Shop.objects.get(user=user)
        user.username=username
        user.email=email
        user.save()
        shop.name=shop_name
        profile.gender=gender
        if avatar:
            profile.avatar=avatar
        profile.phone=phone
        profile.date_of_birth=date_of_birth
        profile.save()
        shop.save()
        return Response({'ol':'ooo'})

def get_count_review(order):
    count=0
    for cart_item in order.items.all():
        count+= ReView.objects.filter(cartitem=cart_item).count()
    return count

class PurchaseAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request):
        limit=5
        from_item=0
        offset=request.GET.get('offset')
        user=request.user
        order_id=request.GET.get('id')
        type_order=request.GET.get('type')
        review=request.GET.get('review')
        if order_id and not review:
            order = Order.objects.get(id=order_id)
            data={
                'cart_item':[{
                'item_image':cart_item.get_image(),'item_url':cart_item.item.get_absolute_url(),
                'item_name':cart_item.item.name,'color_value':cart_item.product.get_color(),
                'size_value':cart_item.product.get_size(),'id':cart_item.id
                } for cart_item in order.items.all()]
            }
            return Response(data)
        elif order_id and review:
            order = Order.objects.get(id=order_id)
            cartitem=order.items.all()
            reviews=ReView.objects.filter(cartitem__in=cartitem).prefetch_related('cartitem__item__media_upload').select_related('cartitem__item').select_related('cartitem__product__size').select_related('cartitem__product__color')
            serializer = ReviewSerializer(reviews,many=True,context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            if offset:
                from_item=int(offset)
            to_item=from_item+limit
            order_all = Order.objects.filter(ordered=True,user=user)
            count_order=order_all.count()
            order_all = order_all[from_item:to_item]
            if type_order=='2':
                order_all=order_all.filter(accepted_date__lt=timezone.now(),canceled=False)
            if type_order=='3':
                order_all=order_all.filter(being_delivered=True)
            if type_order=='4':
                order_all=order_all.filter(received=True)
            if type_order=='5':
                order_all=order_all.filter(canceled=True)
            list_order=[{'shop':{'name':order.shop.name,'url':order.shop.get_absolute_url(),'user_id':order.shop.user_id},'received':order.received,'canceled':order.canceled,
                'being_delivered':order.being_delivered,'shop_url':order.shop.get_absolute_url(),'id':order.id,
                'accepted':order.accepted,'amount':order.total_final_order(),
                'received_date':order.received_date,'review':get_count_review(order),
                'cart_item':[{
                'item_image':cart_item.get_image(),'item_url':cart_item.item.get_absolute_url(),
                'item_name':cart_item.item.name,'color_value':cart_item.product.get_color(),
                'quantity':cart_item.quantity,'discount_price':cart_item.product.total_discount(),
                'size_value':cart_item.product.get_size(),'price':cart_item.product.price,
                'id':cart_item.id
                } for cart_item in order.items.all()]} for order in order_all]
            data={
                'a':list_order,'count_order':count_order,
                }
            return Response(data)
    def post(self,request,*args, **kwargs):
        user=request.user
        file=request.FILES.getlist('file_choice')
        file_update=request.FILES.getlist('file_update')
        reason=request.POST.get('reason')
        order_id=request.POST.get('order_id')
        list_id=request.POST.getlist('id')
        file_id=request.POST.getlist('file_id')
        file_preview=request.FILES.getlist('file_preview')
        file_preview_update=request.FILES.getlist('file_preview_update')
        duration=request.POST.getlist('duration')
        duration_update=request.POST.getlist('duration_update')
        list_preview=[None for  i in range(len(file))]
        list_preview_update=[None for  i in range(len(file_update))]
        for i in range(len(list_preview)):
            for j in range(len(file_preview)):
                if i==j:
                    list_preview[i]=file_preview[j]
        
        total_xu=request.POST.get('total_xu')
        profile=Profile.objects.get(user=user)
        cartitem_id=request.POST.getlist('cartitem_id')
        cartitem=CartItem.objects.filter(id__in=cartitem_id)
        review_rating=request.POST.getlist('review_rating')
        review_text=request.POST.getlist('review_text')
        info_more=request.POST.getlist('info_more')
        anonymous_review=request.POST.getlist('anonymous_review')
        list_anonymous_review=[False if anonymous_review[i]=='false' else True for i in range(len(anonymous_review))]
        rating_bab_category=request.POST.getlist('rating_bab_category')
        if reason:
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
            cart_items = order.items.all()
            cart_items.update(ordered=False)
            for item in cart_items:
                item.save()
                products=Variation.objects.get(id=item.product_id)
                products.inventory += item.quantity
                products.save()
                for byproduct in item.byproduct.all():
                    product=Variation.objects.get(id=byproduct.byproduct_id)
                    product.inventory+=byproduct.quantity
                    product.save()
            data={
                'cancel':'cancel'
            }
            return Response(data)
        else:
            profile.xu=total_xu
            profile.save()
            reviews=ReView.objects.bulk_create([
                ReView(
                    user=user,
                    cartitem=cartitem[i],
                    review_rating=review_rating[i],
                    review_text=review_text[i],
                    info_more=info_more[i],
                    anonymous_review=list_anonymous_review[i],
                    rating_product=int(rating_bab_category[i].split(',')[0]),
                    rating_seller_service=int(rating_bab_category[i].split(',')[1]),
                    rating_shipping_service=int(rating_bab_category[i].split(',')[2]),
                ) for i in range(len(cartitem_id))
            ])

            list_media=Media_review.objects.bulk_create([Media_review(
                upload_by=user,
                file=file[i],
                review=CartItem.objects.get(id=list_id[i]).get_review(),
                file_preview=list_preview[i],
                duration=float(duration[i])
                )
                for i in range(len(file))
                ])
            
            data={'review':'review'}
            return Response(data)

class PasswordResetView(APIView):
    def post(self, request, *args, **kwargs):
        email=request.data.get('email',None)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise NotAcceptable(_("Please enter a valid email."))
        uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
        token = default_token_generator.make_token(user)

        absurl = 'http://localhost:3000/forgot_password/' +uidb64+ '/'+token+'?email='+email
    
        email_body =f"Xin chao {user.username}, \nChúng tôi nhận được yêu cầu thiết lập lại mật khẩu cho tài khoản Anhdai của bạn.\nNhấn tại đây để thiết lập mật khẩu mới cho tài khoản Anhdai của bạn. \n{absurl}"
        data = {'email_body': email_body, 'to_email': user.email,
                    'email_subject': f"Thiết lập lại mật khẩu đăng nhập {user.username}"}
        
        email = EmailMessage(
            subject=data['email_subject'], body=data['email_body'], to=[data['to_email']])
        email.send()
        return Response(
            {"detail": "Password reset e-mail has been sent."},
            status=status.HTTP_200_OK,
        )

class SetNewPasswordAPIView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer
    def post(self, request,*args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'success': True, 'message': 'Password reset success'}, status=status.HTTP_200_OK)

class ChangePasswordView(generics.UpdateAPIView):
    """
    An endpoint for changing password.
    """
    serializer_class = ChangePasswordSerializer
    model = User
    permission_classes = (IsAuthenticated,)

    def get_object(self, queryset=None):
        obj = self.request.user
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


