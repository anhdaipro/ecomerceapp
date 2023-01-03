
# Create your views here.
from twilio.rest import Client
from django.db.models import Q
from django.conf import settings
import requests
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
from django.db.models.functions import Coalesce
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
from categories.models import *
from orders.models import *
from carts.models import *
from discounts.models import *
from chats.models import *
from city.models import *
from myweb.models import *
from account.models import *
from orderactions.models import *
from rest_framework.decorators import api_view
from bulk_update.helper import bulk_update
from .serializers import (ChangePasswordSerializer,UserSerializer,SMSPinSerializer,
SMSPinSerializer,SMSVerificationSerializer,CategorySerializer,SetNewPasswordSerializer,
UserprofileSerializer,ShopinfoSerializer,ItemSerializer,ItemdetailSerializer,
ItemSellerSerializer,ShoporderSerializer,ImagehomeSerializer,ComboSerializer,
CategoryhomeSerializer,AddressSerializer,OrderSerializer,OrderdetailSerializer,
ReviewSerializer,CartitemcartSerializer,CartviewSerializer,
ProductdealSerializer,ItemcomboSerializer,CombodetailseSerializer,ItempageSerializer
,ShopdetailSerializer,OrderpurchaseSerializer,CategorysearchSerializer,
CategorydetailSerializer,VariationcartSerializer,ItemflasaleSerializer,
ByproductdealSerializer,ByproductcartSerializer,ComboItemSerializer,
DealByproductSerializer,FlashSaleinfoSerializer,ReviewitemSerializer
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
import pytz
timezones = pytz.timezone('Asia/Ho_Chi_Minh')
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
    permission_classes = (AllowAny,)
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
class RefreshTokenuser(APIView):
    permission_classes = (AllowAny,)
    def post(self, request,id):
        user=User.objects.get(id=id)
        refresh = RefreshToken.for_user(user)
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'access_expires': timezone.now()+settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']
        }
        return Response(data)
class UpdateOnline(APIView):
    permission_classes = (IsAuthenticated,)
    def post(self,request):
        online=request.data.get('online')
        Profile.objects.filter(user=request.user).update(online=False,is_online=timezone.now())
        return Response({'time':timezone.now()})

class RegisterView(APIView):
    permission_classes = (AllowAny,)
    serializers_class=UserSerializer
    def post(self, request, *args, **kwargs):
        serializer = self.serializers_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class Registeremail(APIView):
    permission_classes = (AllowAny,)
    def post(self,request):
        username=request.data.get('username')
        email=request.data.get('email')
        verify=request.data.get('verify')
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
        otp = int(request.data.get("otp"))
        email=request.data.get('email')
        reset=request.data.get('reset')
        verifyemail=Verifyemail.objects.filter(email=email).last()
        if verifyemail.otp==otp:    
            return Response({'verify':True})
        else:
            return Response({'verify':False})

class Sendotp(APIView):
    permission_classes = (AllowAny,)
    def post(self, request, *args, **kwargs):
        phone=request.data.get('phone')
        login=request.data.get('login')
        reset=request.data.get('reset')
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
        id=request.data.get('id')
        pin = int(request.data.get("pin"))
        phone=request.data.get('phone')
        reset=request.data.get('reset')
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
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')
        token=request.data.get('token')
        user_id=request.data.get('user_id')
        if token:
            token = AccessToken.objects.get(token=token)
            user = token.user
        elif user_id:
            user=User.objects.get(id=user_id)
        else:
            if email:
                user = authenticate(request, email=email, password=password)
            else:
                user = authenticate(request, username=username, password=password)
        try:
            refresh = RefreshToken.for_user(user)
            data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'access_expires': timezone.now()+settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']
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
        flash_sales=Flash_sale.objects.filter(valid_to__gt=timezone.now(),valid_from__lt=timezone.now())
        data={}
        if flash_sales.exists():
            flash_sale=FlashSaleinfoSerializer(flash_sales.first()).data
            data.update(flash_sale)
        list_items=Item.objects.filter(flash_sale__in=flash_sales).prefetch_related('flash_sale').prefetch_related('media_upload').prefetch_related('variation_item__color').prefetch_related('variation_item__size').prefetch_related('cart_item__order_cartitem')[:15]
        data.update({'items_flash_sale':ItemflasaleSerializer(list_items,many=True).data})
        return Response(data)
class ListFlashsaleAPI(APIView):
    permission_classes = (AllowAny,)
    def get(self,request):
        flash_sales=Flash_sale.objects.filter(valid_to__gt=timezone.now()).order_by('valid_from').distinct('valid_from')[:5]
        list_flash_sale=FlashSaleinfoSerializer(flash_sales,many=True).data
        return Response(list_flash_sale)
class FlashsaleAPI(APIView):
    permission_classes = (AllowAny,)
    def get(self,request):
        promotionId=request.GET.get('promotionId')
        list_flash_sales=Flash_sale.objects.filter(valid_to__gt=timezone.now())
        data={}
        if promotionId:
            flash_sale=Flash_sale.objects.get(id=promotionId)
            data.update(FlashSaleinfoSerializer(flash_sale).data)
            list_flash_sales=Flash_sale.objects.filter(valid_from=flash_sale.valid_from)
        if promotionId is None:
            list_flash_sales=list_flash_sales.filter(valid_from__lt=timezone.now())
            if list_flash_sales.exists():
                flash_sale=list_flash_sales.first()
                data.update(FlashSaleinfoSerializer(flash_sale).data)
        list_items=Item.objects.filter(flash_sale__in=list_flash_sales).prefetch_related('flash_sale').prefetch_related('media_upload').prefetch_related('variation_item__color').prefetch_related('variation_item__size').prefetch_related('cart_item__order_cartitem')
        count=list_items.count()
        offset=16
        from_to=request.GET.get('from_to')
        from_item=0
        if from_to:
            from_item=int(from_to)
        to_item=from_item+offset
        if from_item+offset>=count:
            to_item=count
        list_items=list_items[from_item:to_item]
        data.update({'count':count,'items_flash_sale':ItemflasaleSerializer(list_items,many=True,context={'promotionId':promotionId}).data})
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
    serializer_class = CategorysearchSerializer
    def get_queryset(self):
        categories=Category.objects.filter(choice=True).exclude(item=None).annotate(count=Count('item__cart_item__order_cartitem')).order_by('-count')[:20]
        return categories

def search_matching(list_keys):
    q = Q()
    for key in list_keys:
        q |= Q(name__icontains = key)
    return Item.objects.filter(q).values('name').order_by('category__title').distinct()

def get_count(category):
    return Item.objects.filter(category=category).count()

class Topsearch(APIView):
    permission_classes = (AllowAny,)
    def get(self,request):
        keyword=list(SearchKey.objects.all().order_by('-total_searches').values('keyword').filter(updated_on__gte=timezone.now()-timedelta(days=30)))
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

class SearchitemshopAPI(APIView):
    permission_classes = (AllowAny,)
    def get(self,request):
        shop_id=request.GET.get('shop_id')
        minprice=request.GET.get('minPrice')
        maxprice=request.GET.get('maxPrice')
        order=request.GET.get('order')
        sortby=request.GET.get('sortby')
        page=request.GET.get('page')
        categoryID=request.GET.get('categoryID')
        items=Item.objects.filter(shop_id=shop_id)
        if categoryID:
            categoryID=int(categoryID)
            items=items.filter(category__id=categoryID)
        if sortby:
            if sortby=='pop':
                items=items.annotate(count_like= Count('item_likers')).annotate(count_order= Count('cart_item__order_cartitem')).annotate(count_order= Count('cart_item__order_cartitem')).annotate(count_review= Count('cart_item__review_item')).order_by('-count_like','-count_review','-count_order')
            elif sortby=='ctime':
                items=items.annotate(count_order= Count('cart_item__order_cartitem__id')).annotate(count_review= Count('cart_item__review_item')).order_by('-id')
            elif sortby=='price':
                items=items.annotate(avg_price= Avg('variation_item__price')).order_by('avg_price')
                if order=='desc':
                    items=items.annotate(avg_price= Avg('variation_item__price')).order_by('-avg_price')
        paginator = Paginator(items,30)
        page_obj = paginator.get_page(page)
        data={'list_item_page':ItempageSerializer(page_obj,many=True).data,'page_count':paginator.num_pages}
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
        category_id=request.GET.get('category_id')
        shop_id=request.GET.get('shop_id')
        list_items=Item.objects.all()
        items=Item.objects.all()
        list_shop=Shop.objects.all()
        category_choice=Category.objects.filter(choice=True)
        if keyword:
            list_items = list_items.filter(Q(name__icontains=keyword)|Q(shop__name=keyword) | Q(brand__in=keyword)|Q(category__title=keyword)).order_by('name').distinct()
            items = Item.objects.filter(Q(name__icontains=keyword) | Q(
            brand__in=keyword)|Q(category__title=keyword)).prefetch_related('media_upload').prefetch_related('main_product').prefetch_related('promotion_combo').prefetch_related('shop_program').prefetch_related('variation_item__color').prefetch_related('variation_item__size').prefetch_related('cart_item__order_cartitem').distinct()
            category_choice=category_choice.filter(item__in=list_items).order_by('title').distinct()
            list_shop=Shop.objects.filter(item__in=list_items)
            SearchKey.objects.get_or_create(keyword=keyword)
            SearchKey.objects.filter(keyword=keyword).update(total_searches=F('total_searches') + 1)
        if shop_id:
            list_items=list_items.filter(shop_id=shop_id)
            items=items.filter(shop_id=shop_id).distinct()
        if categoryID:
            categoryID=int(categoryID)
            items=items.filter(category__id=categoryID)
        if category_id:
            category_parent=Category.objects.get(id=category_id)
            category_choice=category_parent.get_descendants(include_self=False).filter(choice=True)
            list_items=list_items.filter(Q(category__in=category_choice)|Q(category=category_parent)).distinct()
            items=items.filter(Q(category__in=category_choice)|Q(category=category_parent)).distinct()
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
                items=items.annotate(count_like= Count('item_likers')).annotate(count_order= Count('cart_item__order_cartitem')).annotate(count_order= Count('cart_item__order_cartitem')).annotate(count_review= Count('cart_item__review_item')).order_by('-count_like','-count_review','-count_order')
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
            'category_choice':[{'id':i.id,'title':i.title,'count_item':i.item_set.all().count(),'url':i.slug} for i in category_choice if i.item_set.all().count()>0],
            'list_item_page':ItempageSerializer(page_obj,many=True).data
            ,'page_count':paginator.num_pages
        }
        return Response(data)
        
class ImageHomeAPIView(APIView):
    permission_classes = (AllowAny,)
    
    def get(self,request):
        image_home= Image_home.objects.all()
        return Response(ImagehomeSerializer(image_home,many=True).data)
    def post(self,request):
        list_items=[]
        image=request.FILES.getlist('image')
        url_field=request.POST.getlist('url_field')
        for i in range(len(image)):
            item=Image_home(image=image[i],url_field=url_field[i])
            list_items.append(item)
        Image_home.objects.bulk_create(list_items)
        return Response({"success":True})
class ItemdetailAPI(APIView):
    permission_classes = (AllowAny,)
    def get(self,request):
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        item_id=request.GET.get('itemId')
        item=Item.objects.get(id=item_id)
        item.views += 1
        item.save()
        serializer =ItemdetailSerializer(item,context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK) 
        if token:
            if ItemViews.objects.filter(item=item,user=request.user).filter(create_at__gte=datetime.datetime.now(tz=timezones).replace(hour=0,minute=0,second=0)).count()==0:
                ItemViews.objects.create(item=item,user=request.user)

class ShopdetailAPI(APIView):
    permission_classes = (AllowAny,)
    def get(self,request):
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        item_id=request.GET.get('itemId')
        category_id=request.GET.get('categoryId')
        item=Item.objects.get(id=item_id)
        shop=item.shop
        shop.views += 1
        shop.save()
        serializer =ShopdetailSerializer(shop,context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK) 
        if token:
            user=request.user
            if ShopViews.objects.filter(shop=shop,user=user).filter(create_at__gte=datetime.datetime.now(tz=timezones).replace(hour=0,minute=0,second=0)).count()==0:
                ShopViews.objects.create(shop=shop,user=user)

class CategorydetailAPI(APIView):
    permission_classes = (AllowAny,)
    def get(self, request,slug):
        category=Category.objects.filter(slug=slug)
        if category.exists():
            category=category.first()
            data=CategorydetailSerializer(category).data
            return Response(data)
        else:
            shop=Shop.objects.get(slug=slug)
            shop.views += 1
            shop.save()
            serializer =ShopdetailSerializer(shop,context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK) 
            if token:
                user=request.user
                if ShopViews.objects.filter(shop=shop,user=user).filter(create_at__gte=datetime.datetime.now(tz=timezones).replace(hour=0,minute=0,second=0)).count()==0:
                    ShopViews.objects.create(shop=shop,user=user)
        

class CategoryinfoAPI(APIView):
    permission_classes = (AllowAny,)
    def get(self,request):
        category_id=request.GET.get('category_id')
        category=Category.objects.get(id=category_id)
        category_parent=category.get_root()
        category_children=Category.objects.filter(parent=category_parent,level=1)
        data={
            'category_parent':CategorySerializer(category_parent).data,
            'category_children':CategorySerializer(category_children,many=True).data,
        }
        return Response(data)

class ProductInfoAPI(APIView):
    permission_classes = (AllowAny,)
    def get(self,request,id):
        media=request.GET.get('media')
        review_rating=request.GET.get('review_rating')
        comment=request.GET.get('comment')
        deal=request.GET.get('deal')
        all_review=request.GET.get('all')
        choice=request.GET.get('choice')
        item=Item.objects.get(id=id)
        data={}
        if choice=='deal':
            data.update({'variation_choice':item.get_variation_choice()})
            deal_shock=Buy_with_shock_deal.objects.filter(main_products=item,valid_from__lt=timezone.now(),valid_to__gt=timezone.now()).order_by('valid_to').first()
            deal =DealByproductSerializer(deal_shock,context={"request": request}).data
            data.update(deal)
        elif choice=='combo':
            promotion_combo=Promotion_combo.objects.filter(products=item,valid_from__lt=timezone.now(),valid_to__gt=timezone.now()).first()
            data =ComboItemSerializer(promotion_combo,context={"request": request}).data
        elif choice=='shop':
            shop=item.shop
            data = ShopinfoSerializer(shop,context={"request": request}).data 
        elif choice=='hotsale':
            list_hot_sales=Item.objects.filter(shop_id=item.shop_id,cart_item__order_cartitem__ordered=True).annotate(count=Count('cart_item__order_cartitem__id')).prefetch_related('shop_program').prefetch_related('promotion_combo').prefetch_related('media_upload').prefetch_related('variation_item__color').prefetch_related('variation_item__size').order_by('-count')
            data = ItemSerializer(list_hot_sales,many=True,context={"request": request}).data
        elif choice=='detail':
            detail_item=item.detail
            data=detail_item
        elif choice=='review':
            list_review=ReView.objects.filter(cartitem__product__item=item)
            reviews=list_review
            count_comment= list_review.exclude(info_more='').count()
            count_media= list_review.exclude(media_review=None).count()
            if review_rating:
                reviews=reviews.filter(review_rating=review_rating)
            elif comment:
                reviews=reviews.exclude(info_more='')
            elif media:
                reviews=reviews.exclude(media_review=None)
            paginator = Paginator(reviews, 10)  # Show 25 contacts per page.
            page_number = request.GET.get('page')
            page_obj = paginator.get_page(page_number)
            data={'reviews':ReviewitemSerializer(page_obj,many=True,context={"request": request}).data,
            'page_count':paginator.num_pages,
            'rating':[review.review_rating for review in list_review],'has_comment':count_comment,
            'has_media':count_media
            }
        return Response(data)

    def post(self, request,id, *args, **kwargs):
        user=request.user
        like=True
        data={}
        item=Item.objects.get(id=id)
        liker=Liker.objects.filter(item_id=id,user=request.user)
        if liker.exists():
            liker.delete()
            like=False
        else:
            Liker.objects.create(item_id=id,user=request.user)
        data.update({'num_like':item.num_like(),'like':like})  
        return Response(data)

class ShopinfoAPI(APIView):
    permission_classes = (AllowAny,)
    def get(self,request):
        choice=request.GET.get('choice')
        shop_id=request.GET.get('shop_id')
        data={}
        if choice=='deal':
            deal_shock=Buy_with_shock_deal.objects.filter(shop_id=shop_id,valid_to__gt=timezone.now(),valid_from__lte=timezone.now())
            data=ProductdealSerializer(deal_shock,many=True).data
        elif choice=='combo':
            promotion_combo=Promotion_combo.objects.filter(shop_id=shop_id,valid_to__gt=timezone.now(),valid_from__lte=timezone.now())
            data =ComboItemSerializer(promotion_combo,many=True,context={"request": request}).data
        elif choice=='gettreecategory':
            categorychild=Category.objects.filter(item__shop_id=shop_id).distinct()
            data=CategorySerializer(categorychild,many=True).data
        return Response(data)

    def post(self, request, *args, **kwargs):
        shop_id=request.data.get('shop_id')
        shop=Shop.objects.get(id=shop_id)
        user=request.user
        follow=False
        followers=Follower.objects.filter(user=request.user,shop=shop)
        if followers.exists():
            follow=False
            followers.delete()
        else:
            follow=True
            follower=Follower.objects.create(user=request.user,shop=shop)
            offers=Follower_offer.objects.filter(shop=shop,valid_to__lt=timezone.now(),valid_from__gt=timezone.now())
            if offers.exists():
                follower.follow_offer=offers.first()
            follower.save()
        data={'num_followers':shop.num_follow(),'follow':follow,'online':shop.user.profile.online,
        'num_followers':shop.num_follow(),
        'is_online':shop.user.profile.is_online,'count_product':shop.count_product(),
        'total_review':shop.total_review(),'averge_review':shop.averge_review()}
        return Response(data)

class ListItemRecommendAPIView(APIView):
    permission_classes = (AllowAny,)
    def get(self,request):
        items_recommend=Item.objects.all()
        page_number = request.GET.get('page')
        paginator = Paginator(items_recommend, 30)
        page_obj = paginator.get_page(page_number)
        serializer = ItempageSerializer(page_obj,many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
        
class Itemrecently(ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ItemSerializer
    def get_queryset(self):
        request=self.request
        user=request.user
        itemview=ItemViews.objects.filter(user=user).order_by('-id')
        return Item.objects.filter(item_views__in=itemview)[:12]

class Listitemhostsale(ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ItemSerializer
    def get_queryset(self):
        request=self.request
        item=Item.objects.filter(shop_id=shop_id).filter(cart_item__order_cartitem__ordered=True).annotate(count_order= Count('cart_item__order_cartitem')).prefetch_related('media_upload').prefetch_related('main_product').prefetch_related('promotion_combo').prefetch_related('shop_program').prefetch_related('variation_item__color').prefetch_related('variation_item__size').prefetch_related('cart_item__order_cartitem').order_by('-count_order')
        return item[:10]
    
@api_view(['GET', 'POST'])
def save_voucher(request):
    if request.method=="POST":
        voucher_id=request.data.get('voucher_id')
        Voucheruser.objects.get_or_create(user=request.user,voucher_id=voucher_id)
        data={'ok':'ok'}
        return Response(data)

@api_view(['GET', 'POST'])
def update_image(request):
    if request.method=="POST":
        files=request.FILES.getlist('files')
        category_id=request.POST.get('category_id')
        Image_category.objects.bulk_create(
            [Image_category(
                image=files[i],
                url_field='/kids-babies-fashion-cat'
            ) for i in range(len(files))]
        )
        
        return Response({'success':True})

class Updatecategory(APIView):
    def post(self,request):
        items=request.data.get('items')
        category_id=request.data.get('category_id')
        category=Category.objects.get(id=category_id)
        category.image_category.add(*items)
        return Response({'success':True})
class Category_home(ListAPIView):
    permission_classes = (AllowAny,)
    def get(self,request):
        data=Category.objects.exclude(image=None).order_by('title').values('title').distinct()[:8]
        return Response(data)
    
class CartAPIView(APIView):
    permission_classes = (AllowAny,)
    def get(self,request):
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        if token:
            list_cart_items=CartItem.objects.filter(ordered=False,user=request.user).select_related('item').select_related('product').prefetch_related('item__main_product').prefetch_related('item__promotion_combo')
            cart_item=list_cart_items[0:5]
            count=list_cart_items.count()
            list_cart_item=CartviewSerializer(cart_item,many=True,context={"request": request}).data
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
            'list_item':ItempageSerializer(page_obj,many=True).data
        }
        return Response(data)
    def post(self, request,price=0,total=0,count_cartitem=0,total_discount=0,discount_deal=0,discount_voucher_shop=0,discount_promotion=0,count=0,*args, **kwargs):  
        user=request.user
        item_id=request.data.get('item_id')
        cartitem_id=request.data.get('cartitem_id')
        color_id=request.data.get('color_id')
        size_id=request.data.get('size_id')
        byproduct_id=request.data.get('byproduct_id')
        quantity=request.data.get('quantity')
        data={}
        if item_id and size_id and color_id:
            product=Variation.objects.get(item=item_id,color_id=color_id,size_id=size_id)
        if item_id and color_id and size_id==None:
            product=Variation.objects.get(item=item_id,color_id=color_id)
        if item_id and color_id==None and size_id:
            product=Variation.objects.get(item=item_id,size_id=size_id)
        if item_id and color_id==None:
            product=Variation.objects.get(item=item_id)
        try:
            cart_item=CartItem.objects.get(id=cartitem_id)
            cart_item.product=product
            if quantity:
                cart_item.quantity=quantity
            cart_item.save()
            data.update({'item':{
            'price':cart_item.product.price,
            'color_value':cart_item.product.get_color(),'size_value':cart_item.product.get_size(),
            'total_price':cart_item.total_discount_cartitem(),'inventory':cart_item.product.inventory,
            }})
        except Exception:
            byproduct=Byproduct.objects.get(id=byproduct_id)
            byproduct.product=product
            if quantity:
                cart_item.quantity=quantity
            byproduct.save()
            data.update({'item':{
            'price':byproduct.product.price,
            'total_price':byproduct.total_price(),
            'inventory':byproduct.product.inventory,
            'color_value':byproduct.product.get_color(),'size_value':byproduct.product.get_size()
            }})
        order_check = Order.objects.filter(user=user, ordered=False).exclude(items=None)
        for order in order_check:
            discount_voucher_shop+=order.get_discount_voucher()
            count_cartitem+=order.count_item_cart()
            for cartitem in order.items.all():
                count+=cartitem.count_item_cart()
                total+=cartitem.total_price_cartitem()
                total_discount+=cartitem.total_discount_cartitem()
                discount_deal+=cartitem.save_deal()
                discount_promotion+=cartitem.discount_promotion()  
        data.update({'orders':{
            'total':total,'total_discount':total_discount,'discount_promotion':discount_promotion,
            'discount_deal':discount_deal,'discount_voucher_shop':discount_voucher_shop,'count':count,'count_cartitem':count_cartitem
        }})
        return Response(data)

class AddToCardBatchAPIView(APIView):
    def get(self, request):
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
        data=VariationcartSerializer(product,context={"request": request}).data
        return Response(data)
    def post(self, request, *args, **kwargs):
        user=request.user
        product_id=request.data.get('product_id')
        quantity_product=request.data.get('quantity')
        item_id=request.data.get('item_id')
        byproducts=request.data.get('byproducts')
        deal_id=request.data.get('deal_id')
        action=request.data.get('action')
        variation_choice=Variation.objects.get(id=product_id)
        cartitem=CartItem.objects.filter(user=request.user,product_id=product_id,ordered=False)
        item=Item.objects.get(id=item_id)
        data={}
        if cartitem.exists():
            cartitem=cartitem.last()
            cartitem.deal_shock_id=deal_id
            if action=='add':
                cartitem.quantity+=int(quantity_product)
            else:
                cartitem.quantity=int(quantity_product)
            cartitem.save()
            
        else:
            cartitem=CartItem.objects.create(
                product=variation_choice,
                user=user,
                item_id=item_id,
                ordered=False,
                shop=item.shop,
                deal_shock_id=deal_id,
                quantity=int(quantity_product)
            )
        list_byproduct_cart_delete=[product['byproduct_id'] for product in byproducts if product.get('byproduct_id') and product['check']==False]
        list_product_cart=[product for product in byproducts if  (product.get('byproduct_id')==None and product['check']) or (product.get('byproduct_id') and product['check'])]
        byproduct_update=[]
        byproduct_create=[]
        for product in list_product_cart:
            byproduct_cart=Byproduct.objects.filter(product_id=product['product_id'],cartitem=cartitem,user=request.user)
            if byproduct_cart.exists():
                byproduct_cart=byproduct_cart.first()
                if action=='add':
                    byproduct_cart.quantity+=product['quantity']
                else:
                    byproduct_cart.quantity=product['quantity']
                byproduct_update.append(byproduct_cart)
            else:
                byproduct_create.append(Byproduct(user=user,cartitem=cartitem,item_id=product['item_id'],product_id=product['product_id'],quantity=product['quantity'])
            )
        Byproduct.objects.filter(id__in=list_byproduct_cart_delete).delete()
        Byproduct.objects.bulk_update(byproduct_update,['quantity'],batch_size=1000)
        Byproduct.objects.bulk_create(byproduct_create)
        return Response({'id':cartitem.id})

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
            'price':product.price,'program':product.get_discount_program(),
            'deal':product.get_discount_deal(),
            'discount_price':product.total_discount(),
            'inventory':product.inventory,'id':product.id
            }
        return Response(data)

    def post(self, request, *args, **kwargs):
        user=request.user
        id=request.data.get('id')
        item_id=request.data.get('item_id')
        quantity=request.data.get('quantity')
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
            if int(quantity)>product.inventory:
                return Response({'errorr':True,'message':"over stock"})
            elif user==item.shop.user:
                return Response({'error':True})
            else:
                cart_item=CartItem.objects.create(
                    product=product,
                    item_id=item_id,
                    user=user,
                    ordered=False,
                    quantity=int(quantity),
                    shop=item.shop,
                    deal_shock=item.get_deal_shock_current(),
                    promotion_combo=item.get_combo_current(),
                    flash_sale=item.get_flash_sale_current(),
                    program=item.get_program_current(),
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
        list_cart_item=CartItem.objects.filter(user=request.user,ordered=False).select_related('shop').prefetch_related('item__media_upload').prefetch_related('item__shop_program').prefetch_related('item__main_product').prefetch_related('item__promotion_combo').select_related('product').select_related('product__size').select_related('product__color').prefetch_related('byproduct_cart')
        serializer = CartitemcartSerializer(list_cart_item,many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    def post(self, request,count_cartitem=0,total_price=0,total=0,discount_product=0,discount_deal=0,discount_voucher_shop=0,discount_promotion=0,count=0, *args, **kwargs):
        user=request.user
        byproduct_id_delete=request.data.get('byproduct_id_delete')
        byproduct_id=request.data.get('byproduct_id')
        cartitem_id=request.data.get('cartitem_id')
        cartitem_id_delete=request.data.get('cartitem_id_delete')
        quantity=request.data.get('quantity')
        shop_id=request.data.get('shop_id')
        id_checked=request.data.get('id_checked',[])
        id_check=request.data.get('id_check',[])
        voucher_id=request.data.get('voucher_id')
        voucher_id_remove=request.data.get('voucher_id_remove')
        list_shop_order=[]
        ordered_date = timezone.now()
        if shop_id:
            CartItem.objects.filter(id__in=id_checked).update(check=True)
            CartItem.objects.filter(id__in=id_check).update(check=False)
            order_qs = Order.objects.filter(user=user,ordered=False,shop_id__in=shop_id)
            if order_qs.exists():
                for order in order_qs:
                    if voucher_id:
                        voucher=Voucher.objects.get(id=voucher_id)
                        if voucher.shop_id==order.shop_id:
                            order.voucher=voucher
                            discount_voucher_shop=order.get_discount_voucher()
                    if voucher_id_remove:
                        voucher=Voucher.objects.get(id=voucher_id_remove)
                        if voucher.shop_id==order.shop_id:
                            order.voucher=None
                    list_shop_order.append(order.shop_id)
                    list_cart_item_remove=CartItem.objects.filter(shop_id=order.shop_id,id__in=id_check)
                    order.items.remove(*list_cart_item_remove)
                    list_cart_item_add=CartItem.objects.filter(shop_id=order.shop_id,id__in=id_checked)
                    order.items.add(*list_cart_item_add) 
                bulk_update(order_qs)
                list_shop_remain=list(set(shop_id) - set(list_shop_order))
                if len(list_shop_remain)>0:
                    order = Order.objects.bulk_create([
                    Order(
                        user=user, ordered_date=ordered_date,shop_id=shop) for shop in list_shop_remain]
                        )
                    orders=Order.objects.filter(user=user,ordered=False)[:len(list_shop_remain)]
                    for order in orders:
                        list_cart_item=CartItem.objects.filter(shop_id=order.shop_id,id__in=id_checked)
                        order.items.add(*list_cart_item)
            else:    
                order = Order.objects.bulk_create([
                    Order(
                    user=user, ordered_date=ordered_date,shop_id=shop) for shop in shop_id]
                )
                order_s=Order.objects.filter(ordered=False,user=user)
                for order in order_s:
                    list_cart_item=CartItem.objects.filter(shop_id=order.shop_id,id__in=id_checked)
                    order.items.add(*list_cart_item)
        else:
            if byproduct_id_delete:
                Byproduct.objects.get(id=byproduct_id_delete).delete()
            elif byproduct_id :
                byproduct=Byproduct.objects.get(id=byproduct_id)
                byproduct.quantity=int(quantity)
                byproduct.save()
                total_price=byproduct.total_price()
            elif cartitem_id:
                cartitem=CartItem.objects.get(id=cartitem_id)
                cartitem.quantity=int(quantity)
                cartitem.save()
                total_price=cartitem.total_discount_main()
            else:
                CartItem.objects.get(id=cartitem_id_delete).delete()
                Byproduct.objects.filter(cartitem=None).delete()
        order_check = Order.objects.filter(user=user, ordered=False).exclude(items=None).select_related('voucher').prefetch_related('items__item__media_upload').prefetch_related('items__byproduct_cart').prefetch_related('items__item__main_product').prefetch_related('items__item__promotion_combo').prefetch_related('items__item__shop_program').prefetch_related('items__product__size').prefetch_related('items__product__color')
        for order in order_check:
            discount_voucher_shop+=order.get_discount_voucher()
            count_cartitem+=order.count_cartitem()
            discount_deal+=order.discount_deal()
            discount_promotion+=order.discount_promotion()
            discount_product+=order.discount_product()
            total+=order.total_price_order()
            count+=order.count_item_cart()
        data={
            'discount_voucher_shop':discount_voucher_shop,'list_shop_order':list_shop_order,
            'total_price':total_price,'count':count,'total':total,'discount_deal':discount_deal,
            'discount_product':discount_product,'count_cartitem':count_cartitem,
            'discount_promotion':discount_promotion
            }
        return Response(data)

class ListorderAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request):
        user=request.user
        order_check = Order.objects.filter(user=user, ordered=False).select_related('shop').select_related('voucher').prefetch_related('items__byproduct_cart').prefetch_related('items__item__main_product').prefetch_related('items__item__promotion_combo').prefetch_related('items__item__shop_program').prefetch_related('items__product').exclude(items=None)
        data=[{'discount_voucher_shop':order.get_discount_voucher(),'total':order.total_price_order(),
            'discount_deal':order.discount_deal(),'count':order.count_item_cart(),
            'count_cartitem':order.count_cartitem(),'shop_id':order.shop_id,
            'discount_promotion':order.discount_promotion(),'discount_product':order.discount_product(),
            'voucher':order.get_voucher()} 
            for order in order_check]
        
        return Response(data,status=status.HTTP_200_OK)

class CityAPI(APIView):
    def get(self,request):
        list_city=City.objects.all()
        return Response(list_city.values())
    def post(self,request):
        cities=request.data.get('cities')
        list_city=[]
        for city in cities:
            list_city.append(City(level=city['level'],matp=city.get('matp'),maqh=city.get('maqh'),name=city['name']))
        City.objects.bulk_create(list_city)
        return Response({'success':True})

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
        city=request.data.get('city')
        district=request.data.get('district')
        town=request.data.get('town')
        phone_number=request.data.get('phone_number')
        name=request.data.get('name')
        default=request.data.get('default')
        address_choice=request.data.get('address_choice')
        address_detail=request.data.get('address')
        address_type=request.data.get('address_type')
        id=request.data.get('id')
        action=request.data.get('action')
        default_address=False
        if action=='default':
            default_address=True
        if id:
            address=Address.objects.get(id=id)
            if action=='update':
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
            elif action=='default':
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
                default=default,
                name=name,
                phone_number=phone_number,
                city=city,
                town=town,
                district=district,
                address_type=address_type,
                address=address_detail
            )
            
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
        user=request.user
        review=ReView.objects.get(id=id)
        image=request.FILES.getlist('image')
        file_id=request.POST.getlist('file_id')
        video=request.FILES.getlist('video')
        video_preview=request.FILES.getlist('video_preview')
        duration=request.POST.getlist('duration')
        review_rating=request.POST.get('review_rating')
        review_text=request.POST.get('review_text')
        info_more=request.POST.get('info_more')
        anonymous_review=request.POST.get('anonymous_review')
        rating_bab_category=request.POST.get('rating_bab_category')
        reason=request.POST.get('reason')
        action=request.POST.get('action')
        data={}
        if action=='update':
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
            list_video=[Media_review(
                upload_by=user,
                file=video[i],
                review_id=id,
                media_preview=video_preview[i],
                duration=float(duration[i])
                )
                for i in range(len(video))
            ]
            list_image=[Media_review(
                upload_by=user,
                file=image[i],
                review_id=id
                )
                for i in range(len(image))
                ]
            
            listmedia=list_video+list_image
            Media_review.objects.bulk_create(listmedia)
            serializer = ReviewSerializer(review,context={"request": request})
            data=serializer.data
        elif action=='report':
            if Report.objects.filter(user=user,review=review).exists():
                Report.objects.filter(user=user,review=review).update(reson=reason)
            else:
                Report.objects.create(user=user,reson=reason,review=review)
            data.update({'report':True})
        else:
            liked=True
            if user in review.like.all():
                liked=False
                review.like.remove(user)  
            else:
                review.like.add(user)  
            data.update({'liked':liked,'num_liked':review.num_like()}) 
        return Response(data) 

class CheckoutAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request):
        user=request.user
        orders = Order.objects.filter(user=user, ordered=False).select_related('shop').select_related('voucher').prefetch_related('items__byproduct_cart').prefetch_related('items__item__media_upload').prefetch_related('items__item__main_product').prefetch_related('items__item__promotion_combo').prefetch_related('items__item__shop_program').prefetch_related('items__product__size').prefetch_related('items__product__color').exclude(items=None)
        serializer = OrderSerializer(orders,many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        user=request.user
        address_id=request.data.get('address_id')
        payment_option=request.data.get('payment_choice')
        orders=request.data.get('orders')
        total=0
        data={'success':True}
        list_orders=[]
        if payment_option == 'Paypal':
            for item in orders:
                order=Order.objects.get(id=item['id'])
                order.shipping_address_id = address_id
                order.shipping_id=item['shipping']['id']
                order.amount=order.total_final_order()+item['fee_shipping']
                list_orders.append(order)
            bulk_update(list_orders)
            payment=Payment.objects.create(user=user,payment_method="P",
            amount=total,paid=False
            )
            payment.order.add(*list_orders)
            data={'a':'a'}
            return Response(data)
        else:
            for item in orders:
                order=Order.objects.get(id=item['id'])
                order.shipping_address_id = address_id
                if order.get_discount_voucher()>0:
                    order.discount_voucher=order.get_discount_voucher()
                else:
                    order.voucher=None
                order.accepted_date=timezone.now()+timedelta(minutes=30)
                order.payment_choice=payment_option
                items = order.items.all()
                id_remove=[item.id for item in items if item.quantity>item.product.inventory]
                id_delete=[item.id for item in items if item.product.inventory==0]
                id_checkout=[item.id for item in items if item.quantity<=item.product.inventory]
                items_checkout=items.filter(id__in=id_checkout)
                items.filter(id__in=id_delete).delete()
                order.items.remove(*id_remove)
                order.ordered=True
                order.amount=order.total_final_order()+item['fee_shipping']
                order.ref_code = create_ref_code()
                order.ordered_date=timezone.now()
                order.shipping_id=item['shipping']['id']
                if len(id_remove)>0:
                    data.update({'message':"Some product had removed from order because it out of stock",waring:True})
                for item in items_checkout:
                    products=Variation.objects.get(id=item.product_id)
                    products.inventory -= item.quantity
                    item.amount_main_products=item.total_discount_main() 
                    item.amount_byproducts=item.total_discount_deal()
                    if not item.get_flash_sale_current():
                        item.flash_sale=None
                    if not item.get_combo_current():
                        item.promotion_combo=None
                    if not item.get_program_current():
                        item.program=None
                    item.ordered=True
                    item.save()
                    products.save()
                    if item.get_deal_shock_current():
                        for byproduct in item.byproduct_cart.all():
                            product=Variation.objects.get(id=byproduct.product_id)
                            product.inventory -= byproduct.quantity
                            product.save()
                    if products.get_discount_flash_sale():
                        flash_sale=products.item.get_flash_sale_current()
                        variations=flash_sale.variations
                        for variation in variations:
                            if variation['variation_id']==products.id:
                                variation=variation.update({'inventory':variation['inventory']-item.quantity,'promotion_stock':variation['promotion_stock']-item.quantity})     
                        flash_sale.variations=variations
                        flash_sale.save()
                    if products.get_discount_program():
                        program=products.item.get_program_current()
                        variations=program.variations
                        for variation in variations:
                            if variation['variation_id']==products.id:
                                variation=variation.update({'inventory':variation['inventory']-item.quantity,'promotion_stock':variation['promotion_stock']-item.quantity})
                        program.variations=variations
                        program.save()
                    
                list_orders.append(order)
                email_body = f"Hello {user.username}, \n {order.shop.user.username} cảm ơn bạn đã đặt hàng"
                data = {'email_body': email_body, 'to_email': user.email,
                    'email_subject': 'Thanks order!'}
                email = EmailMessage(
                subject=data['email_subject'], body=data['email_body'], to=[data['to_email']])
                email.send() 
            bulk_update(list_orders)
            return Response(data)
            
class OrderinfoAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request,id):
        user=request.user
        order=Order.objects.get(id=id)
        serializer = OrderdetailSerializer(order,context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    def post(self,request,id):
        order=Order.objects.get(id=id)
        order.accepted=True
        order.accepted_date=timezone.now()
        order.save()
        return Response({'success':True})

class PaymentAPIView(APIView):
    def get(self,request):
        orders = Order.objects.filter(user=user, ordered=False)
        amount=0
        for order in orders:
            amount+=order.total_final_order()
        return Response({'amount':amount}) 
    def post(self,request): 
        user=request.user
        pay_id=request.data.get('payID')
        payment=Payment.objects.filter(paid=False,user=user).last()
        payment.payment_number=pay_id
        payment.paid=True
        payment.save()
        list_orders = Order.objects.filter(user=user, ordered=False)
        data={}
        for order in list_orders:
            order.ordered_date=timezone.now()
            if order.get_discount_voucher()>0:
                order.discount_voucher=order.get_discount_voucher()
            else:
                order.voucher=None
            order.payment_choice="Paypal"
            order.payment_number=pay_id
            items = order.items.all()
            id_remove=[item.id for item in items if item.quantity>item.product.inventory]
            id_checkout=[item.id for item in items if item.quantity<=item.product.inventory]
            items_checkout=items.filter(id__in=id_checkout)
            order.items.remove(*id_remove)
            id_delete=[item.id for item in items if item.product.inventory==0]
            items.filter(id__in=id_delete).delete()
            order.ordered=True
            order.amount=order.total_final_order()
            order.ref_code = create_ref_code()
            if len(id_remove)>0:
                data.update({'message':"Some product had removed from order because it out of stock",waring:True})
            for item in items_checkout:
                products=item.product
                products.inventory -= item.quantity
                item.amount_main_products=item.total_discount_main() 
                item.amount_byproducts=item.total_discount_deal()
                item.ordered=True
                if not item.get_flash_sale_current():
                    item.flash_sale=None
                if not item.get_combo_current():
                    item.promotion_combo=None
                if not item.get_program_current():
                    item.program=None
                item.save()
                products.save()
                if item.get_deal_shock_current():
                    for byproduct in item.byproduct_cart.all():
                        product=Variation.objects.get(id=byproduct.product_id)
                        product.inventory -= byproduct.quantity
                        product.save()
                if products.get_discount_flash_sale():
                    flash_sale=products.item.get_flash_sale_current()
                    variations=flash_sale.variations
                    
                    for variation in variations:
                        if variation['variation_id']==products.id:
                           
                            variation=variation.update({'inventory':variation['inventory']-item.quantity,'promotion_stock':variation['promotion_stock']-item.quantity})
                    flash_sale.variations=variations
                    flash_sale.save()
                        
                if products.get_discount_program():
                    program=products.item.get_program_current()
                    variations=program.variations
                    for variation in variations:
                        if variation['variation_id']==products.id:
                           
                            variation=variation.update({'inventory':variation['inventory']-item.quantity,'promotion_stock':variation['promotion_stock']-item.quantity})
                    program.variations=variations
                    program.save()
                    
                
            email_body = f"Hello {user.username}, \n {order.shop.user.username} cảm ơn bạn đã đặt hàng"
            data = {'email_body': email_body, 'to_email': user.email,
                    'email_subject': 'Thanks order!'}
            email = EmailMessage(
            subject=data['email_subject'], body=data['email_body'], to=[data['to_email']])
            email.send() 
        data.update({'sucess':True})
        bulk_update(list_orders)
        Payment.objects.filter(paid=False,user=user).delete()
        return Response(data)
     
class Byproductdeal(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request,id):
        from_item=0
        cart_id=request.GET.get('cart_id')
        list_id=[]
        if cart_id:
            cartitem=CartItem.objects.get(id=cart_id)
            for byproduct in cartitem.byproduct_cart.all():
                list_id.append(byproduct.item_id)
        offset=request.GET.get('offset')
        if offset:
            from_item=int(offset)
        deal_shock=Buy_with_shock_deal.objects.get(id=id)
        byproductdeal=deal_shock.byproducts.all().exclude(id__in=list_id)
        count=byproductdeal.count()
        to_item=from_item+10
        if from_item+10>=count:
            to_item=count
        listitem=byproductdeal[from_item:to_item]
        byproducts=ByproductdealSerializer(listitem,many=True).data
        data={'byproducts':byproducts,'count':count}
        return Response(data)

class DealShockAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request,deal_id,id):
        user=request.user
        variation=Variation.objects.get(id=id)
        cartitem_id=None
        cart_item=[]
        byproducts=[]
        variation_choice={
            'product_id':variation.id,'color_value':variation.get_color(),'size_value':variation.get_size(),
            'item_id':variation.item_id,'name':variation.item.name,'check':True,'main':True,
            'price':variation.price,'discount_price':variation.total_discount(),'url':variation.item.slug,
            'sizes':variation.item.get_size(),'inventory':variation.inventory,
            'image':variation.get_image(),'quantity':1,'count_variation':variation.item.count_variation(),
            'colors':variation.item.get_color()}
        cartitem=CartItem.objects.filter(product=variation,ordered=False,user=user)
        if cartitem.exists():
            cartitem=cartitem.last()
            variation_choice.update({'quantity':cartitem.quantity})
            cartitem_id=cartitem.id
            if cartitem.deal_shock_id and cartitem.deal_shock_id!=deal_id:
                Byproduct.objects.filter(cartitem=cartitem).delete()
            else:
                byproducts=ByproductcartSerializer(cartitem.byproduct_cart.all(),many=True).data
        data={
            'cartitem_id':cartitem_id,'deal_id':deal_id,
            'byproducts':byproducts,'variation_choice':variation_choice
        }
        return Response(data)

class PromotionAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request,id):
        promotion=Promotion_combo.objects.get(id=id)
        serializer = CombodetailseSerializer(promotion,context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

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

class ProfileAPI(APIView):
    permission_classes = (IsAuthenticated,)
    def get(self,request):
        user=request.user
        shop_name=None
        count_product=0
        if Shop.objects.filter(user=user).exists():
            shop_name=Shop.objects.filter(user=user).first().name
            count_product=Shop.objects.filter(user=user).first().count_product()
        data={
            'username':user.username,'name':user.profile.name,'email':user.email,
            'phone':str(user.profile.phone),'date_of_birth':user.profile.date_of_birth,
            'avatar':user.profile.avatar.url,'shop_name':shop_name,'bio':user.profile.bio,
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
        bio=request.POST.get('bio')
        date_of_birth=request.POST.get('date_of_birth')
        user=request.user
        profile=Profile.objects.get(user=user)
        shop=Shop.objects.get(user=user)
        if username:
            user.username=username
        if email:
            user.email=email
        user.save()
        if shop_name:
            shop.name=shop_name
        if gender:
            profile.gender=gender
        if avatar:
            profile.avatar=avatar
        if phone:
            profile.phone=phone
        if bio:
            profile.bio=bio
        if name:
            profile.name=name
        if date_of_birth:
            profile.date_of_birth=date_of_birth
        profile.save()
        shop.save()
        return Response({'success':True})

def get_review(order):
    review= ReView.objects.filter(cartitem__order_cartitem=order)
    if review.exists():
        return True

class BuyagainAPI(APIView):
    permission_classes = (IsAuthenticated,)
    def post(self,request):
        product_id=request.data.get('product_id')
        shop_id=request.data.get('shop_id')
        product=Variation.objects.filter(id__in=product_id)
        cartuser=CartItem.objects.filter(user=request.user,ordered=False,product_id__in=product_id)
        list_id=list()
        for cart in cartuser:
            cart.quantity+=1
            list_id.append(cart.product_id)
        productremain=product.exclude(id__in=list_id)
        bulk_update(cartuser)
        CartItem.objects.bulk_create([CartItem(
            product=product,
            user=request.user,
            item_id=product.item_id,
            shop_id=shop_id,
            deal_shock=product.item.get_deal_shock_current(),
            promotion_combo=product.item.get_combo_current(),
            flash_sale=product.item.get_flash_sale_current(),
            program=product.item.get_program_current(),
            quantity=1
        ) for product in productremain])
        return Response({'ok':'ok'})

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
        if order_id and review:
            order = Order.objects.get(id=order_id)
            cartitem=order.items.all()
            reviews=ReView.objects.filter(cartitem__in=cartitem).prefetch_related('cartitem__item__media_upload').select_related('cartitem__item').select_related('cartitem__product__size').select_related('cartitem__product__color')
            serializer = ReviewSerializer(reviews,many=True,context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            order_all = Order.objects.filter(ordered=True,user=user)
            
            if type_order=='2':
                order_all=order_all.filter(accepted_date__lt=timezone.now(),canceled=False,received=False)
            if type_order=='3':
                order_all=order_all.filter(accepted=True,received=False)
            if type_order=='4':
                order_all=order_all.filter(being_delivered=True,received=False)
            if type_order=='5':
                order_all=order_all.filter(received=True)
            if type_order=='6':
                order_all=order_all.filter(canceled=True)
            if type_order=='7':
                order_all=order_all.filter(received=True,refund_granted=True)
            count=order_all.count()
            if offset:
                from_item=int(offset)
            to_item=from_item+limit
            if from_item+limit>=count:
                to_item=count
            order_display = order_all[from_item:to_item]
            data={
                'orders':OrderpurchaseSerializer(order_display,many=True).data,'count':count,
                }
            return Response(data)
    def post(self,request,*args, **kwargs):
        user=request.user
        reason=request.POST.get('reason')
        order_id=request.POST.get('order_id')
        list_id_image=request.POST.getlist('id_image')
        list_id_video=request.POST.getlist('id_video')
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
            cart_items.update(ordered=False,flash_sale=None,program=None,promotion_combo=None)
            for item in cart_items:
                if item.item.get_flash_sale_current():
                    item.flash_sale=item.item.get_flash_sale_current()
                if item.item.get_combo_current():
                    item.promotion_combo=item.item.get_combo_current()
                if  item.item.get_program_current():
                    item.program=item.item.get_program_current()
                item.save()
                products=Variation.objects.get(id=item.product_id)
                products.inventory += item.quantity
                products.save()
                if products.get_discount_flash_sale():
                    flash_sale=products.item.get_flash_sale_current()
                    variations=flash_sale.variations
                   
                    for variation in variations:
                        if variation['variation_id']==products.id:
                            
                            variation=variation.update({'inventory':variation['inventory']+item.quantity,'promotion_stock':variation['promotion_stock']+item.quantity})
                    flash_sale.variations=variations
                    flash_sale.save()
                        
                if products.get_discount_program():
                    program=products.item.get_program_current()
                    variations=program.variations
                    for variation in variations:
                        if variation['variation_id']==products.id:   
                            variation=variation.update({'inventory':variation['inventory']+item.quantity,'promotion_stock':variation['promotion_stock']+item.quantity})
                    program.variations=variations
                    program.save()
                if item.get_deal_shock_current():
                    for byproduct in item.byproduct_cart.all():
                        product=Variation.objects.get(id=byproduct.product_id)
                        product.inventory+=byproduct.quantity
                        product.save()
            data={
                'success':True
            }
            return Response(data)
        else:
            image=request.FILES.getlist('image')
            video_preview=request.FILES.getlist('video_preview')
            duration=request.POST.getlist('duration')
            video=request.FILES.getlist('video')
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
            
            list_video=[Media_review(
                upload_by=user,
                file=video[i],
                review=CartItem.objects.get(id=list_id_video[i]).get_review(),
                media_preview=video_preview[i],
                duration=float(duration[i])
                )
                for i in range(len(video))
            ]
            list_image=[Media_review(
                upload_by=user,
                file=image[i],
                review=CartItem.objects.get(id=list_id_image[i]).get_review()
                )
                for i in range(len(image))
            ]
            listmedia=list_video+list_image
            Media_review.objects.bulk_create(listmedia)
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


