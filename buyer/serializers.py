from rest_framework import serializers
from shop.models import *
from carts.models import *
from category.models import *
from myweb.models import *
from account.models import *
from chats.models import *
from django.contrib import auth
from djoser.serializers import UserCreateSerializer
import datetime
from datetime import timedelta
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, force_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
class UserCreateSerializer(UserCreateSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'password')

class UserprofileSerializer(serializers.ModelSerializer):
    avatar=serializers.SerializerMethodField()
    count_message_unseen=serializers.SerializerMethodField()
    count_notifi_unseen=serializers.SerializerMethodField()
    class Meta:
        model=User
        fields = ('username','id','avatar','count_message_unseen','count_notifi_unseen',)
    def get_avatar(self,obj):
        return obj.profile.avatar.url
    def get_count_notifi_unseen(self,obj):
        return obj.profile.count_notifi_unseen
    def get_count_message_unseen(self,obj):
        return Member.objects.filter(user=obj,is_seen=False).count()

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model=Profile
        fields = ('phone',)

class Verifyemail(serializers.ModelSerializer):
    model = Verifyemail
    fields=['otp','email']

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password','profile']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        profile_data = validated_data.pop('profile', None)  
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        if Profile.objects.filter(user=instance).exists():
            Profile.objects.filter(user=instance).update(**profile_data)
        return instance

class SMSPinSerializer(serializers.Serializer):
    pin = serializers.IntegerField()

class SMSVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMSVerification
        exclude = "modified"

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model=Category
        fields=('title',)

class CategoryhomeSerializer(serializers.ModelSerializer):
    image=serializers.SerializerMethodField()
    url=serializers.SerializerMethodField()
    class Meta:
        model=Category
        fields=('title','url','image',)
    def get_url(self,obj):
        return obj.get_absolute_url()
    def get_image(self,obj):
        if obj.image:
            return obj.image.url

class ChangePasswordSerializer(serializers.Serializer):
    model = User
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(
        min_length=6, max_length=68, write_only=True)
    token = serializers.CharField(
        min_length=1, write_only=True)
    uidb64 = serializers.CharField(
        min_length=1, write_only=True)

    class Meta:
        fields = ['password', 'token', 'uidb64']

    def validate(self, attrs):
        try:
            password = attrs.get('password')
            token = attrs.get('token')
            uidb64 = attrs.get('uidb64')
            id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed('The reset link is invalid', 401)

            user.set_password(password)
            user.save()

            return (user)
        except Exception as e:
            raise AuthenticationFailed('The reset link is invalid', 401)
        return super().validate(attrs)
        
class ImagehomeSerializer(serializers.ModelSerializer):
    image=serializers.SerializerMethodField()
    class Meta:
        model=Image_home
        fields=(
            'image',
            'url_field',
        )
    def get_image(self,obj):
        return obj.image.url

class ItemrecentlySerializer(serializers.ModelSerializer):
    image=serializers.SerializerMethodField()
    max_price=serializers.SerializerMethodField()
    min_price=serializers.SerializerMethodField()
    class Meta:
        model = ItemViews
        fields = (
            'id',
            'image',
            'max_price',
            'min_price',
        )
    
    def get_image(self,obj):
        return obj.item.get_image_cover()
    def get_max_price(self,obj):
        return obj.item.max_price()
    def get_min_price(self,obj):
        return obj.item.min_price()

class ShopinfoSerializer(serializers.ModelSerializer): 
    avatar=serializers.SerializerMethodField()
    url=serializers.SerializerMethodField()
    online=serializers.SerializerMethodField()
    num_follow=serializers.SerializerMethodField()
    count_product=serializers.SerializerMethodField()
    is_online=serializers.SerializerMethodField()
    total_order=serializers.SerializerMethodField()
    class Meta:
        model=Shop
        fields=('id','avatar','url','name','online','num_follow','is_online',
        'count_product','total_order',)
    def get_avatar(self,obj):
        return obj.user.profile.avatar.url
    def get_url(self,obj):
        return obj.get_absolute_url()
    def get_online(self,obj):
        return obj.user.profile.online
    def get_is_online(self,obj):
        return obj.user.profile.online
    def get_count_product(self,obj):
        return obj.count_product()
    def get_total_order(self,obj):
        return obj.total_order()
    def get_num_follow(self,obj):
        return obj.num_follow()

class VoucherSerializer(serializers.ModelSerializer): 
    exists=serializers.SerializerMethodField()
    class Meta:
        model=Voucher
        fields=('id','amount','created','discount_type','maximum_discount','maximum_usage',
        'minimum_order_value','percent','valid_from','valid_to','voucher_type','exists',)
    def get_exists(self,obj):
        request=self.context.get("request")
        if request.user in obj.user.all():
            return True
class ShoporderSerializer(serializers.ModelSerializer): 
    listvoucher=serializers.SerializerMethodField()
    class Meta:
        model=Shop
        fields=('id','name','listvoucher','user_id',)
    def get_listvoucher(self,obj):
        request=self.context.get("request")
        cartview=CartItem.objects.filter(shop=obj,ordered=False)
        list_voucher=Voucher.objects.filter(product__cart_item__in=cartview).distinct()
        return VoucherSerializer(list_voucher,many=True,context={"request": request}).data

class AddressSerializer(serializers.ModelSerializer): 
    class Meta:
        model=Address
        fields = '__all__'

class ItemSellerSerializer(serializers.ModelSerializer):
    image=serializers.SerializerMethodField()
    count_order=serializers.SerializerMethodField()
    class Meta:
        model = Item
        fields = (
            'id',
            'image',
            'count_order',
        )
    def get_image(self,obj):
        return obj.get_image_cover()
    def get_count_order(self,obj):
        return obj.number_order()

class ItemSerializer(serializers.ModelSerializer):
    image=serializers.SerializerMethodField()
    url=serializers.SerializerMethodField()
    max_price=serializers.SerializerMethodField()
    min_price=serializers.SerializerMethodField()
    percent_discount=serializers.SerializerMethodField()
    number_order=serializers.SerializerMethodField()
    class Meta:
        model = Item
        fields = (
            'id',
            'image',
            'max_price',
            'min_price',
            'url',
            'number_order'
            'percent_discount'
        )
    def get_url(self,obj):
        return obj.get_absolute_url()
    def get_image(self,obj):
        return obj.get_image_cover()
    def get_max_price(self,obj):
        return obj.max_price()
    def get_min_price(self,obj):
        return obj.min_price()
    def get_percent_discount(self,obj):
        return obj.percent_discount()
    def get_number_order(self,obj):
        return obj.number_order()

class ItemdetailSerializer(serializers.ModelSerializer):
    shop=serializers.SerializerMethodField()
    percent_discount = serializers.SerializerMethodField()
    category=serializers.SerializerMethodField()
    list_media=serializers.SerializerMethodField()
    list_voucher=serializers.SerializerMethodField()
    shock_deal_type=serializers.SerializerMethodField()
    list_promotion=serializers.SerializerMethodField()
    class Meta:
        model = Item
        fields = (
            'id',
            'name',
            'shop',
            'slug',
            'category',
            'description',
            'percent_discount',
            'list_media',
            'list_voucher',
            'shock_deal_type',
            'list_promotion',
            'max_price',
            'min_price',
            'percent_discount'
        )
    
    def get_shop(self,obj):
        return obj.shop.name
    def get_category(self,obj):
        return obj.category.title
    def get_percent_discount(self,obj):
        return obj.percent_discount()
    def get_list_media(self,obj):
        return obj.get_media()
    def get_list_voucher(self,obj):
        return obj.get_voucher()
    def get_list_promotion(self,obj):
        return obj.get_promotion()
    def get_shock_deal_type(self,obj):
        return obj.shock_deal_type()

class VariationSerializer(serializers.ModelSerializer):
    item = serializers.SerializerMethodField()
    class Meta:
        model = Variation
        fields = (
            'id',
            'color',
            'size',
        )
    def get_item(self, obj):
        return ItemSerializer(obj.item).data

class CartviewSerializer(serializers.ModelSerializer):
    item_name = serializers.SerializerMethodField()
    item_url=serializers.SerializerMethodField()
    item_image=serializers.SerializerMethodField()
    price=serializers.SerializerMethodField()
    promotion=serializers.SerializerMethodField()
    shock_deal_type=serializers.SerializerMethodField()
    class Meta:
        model=('id','item_id','item_name','item_image','item_url',
                'price','shock_deal_type','promotion',)
    
    def get_item_image(self,obj):
        return obj.get_image()
    def get_item_name(self,obj):
        return obj.item.name
    def get_item_url(self,obj):
        return obj.item.get_absolute_url()
    def get_price(self,obj):
        return obj.product.price-obj.product.total_discount()
    def get_promotion(self,obj):
        return obj.item.get_promotion()
    def get_shock_deal_type(self,obj):
        return obj.item.shock_deal_type()

class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model=Shop
        fields=('id','name','user_id',)

class OrderdetailSerializer(serializers.ModelSerializer):
    address=serializers.SerializerMethodField()
    shop=serializers.SerializerMethodField()
    total=serializers.SerializerMethodField()
    cart_item=serializers.SerializerMethodField()
    discount_voucher=serializers.SerializerMethodField()
    total_final=serializers.SerializerMethodField()
    count=serializers.SerializerMethodField()
    fee_shipping=serializers.SerializerMethodField()
    discount_promotion=serializers.SerializerMethodField()
    total_discount=serializers.SerializerMethodField()
    class Meta:
        model=Order
        fields=('cart_item','discount_voucher','total','total_final','shop',
        'address','received','canceled','accepted','amount',
        'being_delivered','ordered_date','received_date',
        'canceled_date','accepted_date',
        'count','fee_shipping','id','discount_promotion','total_discount',)
    def get_shop(self,obj):
        return ShopSerializer(obj.shop).data
    def get_address(self,obj):
        return AddressSerializer(obj.shipping_address).data
    def get_cart_item(self,obj):
        return CartItemSerializer(obj.items.all(),many=True).data
    def get_discount_voucher(self,obj):
        return obj.discount_voucher()
    def get_total(self,obj):
        return obj.total_price_order()
    def get_total_final(self,obj):
        return obj.total_final_order()
    def get_count(self,obj):
        return obj.count_item_cart()
    def get_fee_shipping(self,obj):
        return obj.fee_shipping()
    def get_discount_promotion(self,obj):
        return obj.discount_promotion()
    def get_total_discount(self,obj):
        return obj.total_discount_order()

class OrderSerializer(serializers.ModelSerializer):
    shop=serializers.SerializerMethodField()
    total=serializers.SerializerMethodField()
    cart_item=serializers.SerializerMethodField()
    discount_voucher=serializers.SerializerMethodField()
    total_final=serializers.SerializerMethodField()
    count=serializers.SerializerMethodField()
    fee_shipping=serializers.SerializerMethodField()
    discount_promotion=serializers.SerializerMethodField()
    total_discount=serializers.SerializerMethodField()
    class Meta:
        model=Order
        fields=('cart_item','discount_voucher','total','total_final','shop','amount',
        'count','fee_shipping','id','discount_promotion','total_discount',)
    def get_shop(self,obj):
        return ShopSerializer(obj.shop).data
    
    def get_cart_item(self,obj):
        return CartItemSerializer(obj.items.all(),many=True).data
    def get_discount_voucher(self,obj):
        return obj.discount_voucher()
    def get_total(self,obj):
        return obj.total_price_order()
    def get_total_final(self,obj):
        return obj.total_final_order()
    def get_count(self,obj):
        return obj.count_item_cart()
    def get_fee_shipping(self,obj):
        return obj.fee_shipping()
    def get_discount_promotion(self,obj):
        return obj.discount_promotion()
    def get_total_discount(self,obj):
        return obj.total_discount_order()

class MediareviewSerializer(serializers.ModelSerializer):
    filetype = serializers.SerializerMethodField()
    file = serializers.SerializerMethodField()
    media_preview = serializers.SerializerMethodField()
    show=serializers.SerializerMethodField()
    class Meta:
        model=Media_review
        fields=('id','duration','filetype','media_preview','file','show',)
    def get_filetype(self,obj):
        return obj.filetype()
    def get_file(self,obj):
        return obj.file.url
    def get_media_preview(self,obj):
        return obj.get_media_preview()
    def get_show(self,obj):
        return False

class ReviewSerializer(serializers.ModelSerializer):
    color_value = serializers.SerializerMethodField()
    size_value = serializers.SerializerMethodField()
    item_image = serializers.SerializerMethodField()
    item_name = serializers.SerializerMethodField()
    item_url = serializers.SerializerMethodField()
    list_file=serializers.SerializerMethodField()
    rating_bab_category=serializers.SerializerMethodField()
    class Meta:
        model=ReView
        fields=('id','review_text','created','item_name','color_value','size_value',
                'info_more','anonymous_review','list_file','item_url','item_image',
                'rating_bab_category','review_rating','edited',)
    def get_list_file(self,obj):
        return MediareviewSerializer(obj.media_review.all(),many=True).data  
    def get_color_value(self,obj):
        return obj.cartitem.product.get_color()
    def get_rating_bab_category(self,obj):
        return [obj.rating_product,obj.rating_seller_service,obj.rating_shipping_service]
    def get_size_value(self,obj):
        return obj.cartitem.product.get_size()
    def get_item_image(self,obj):
        return obj.cartitem.get_image()
    def get_item_name(self,obj):
        return obj.cartitem.item.name
    def get_item_url(self,obj):
        return obj.cartitem.item.get_absolute_url()

class ByproductSerializer(serializers.ModelSerializer):
    color_value = serializers.SerializerMethodField()
    size_value = serializers.SerializerMethodField()
    item_image = serializers.SerializerMethodField()
    item_name = serializers.SerializerMethodField()
    item_url = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    class Meta:
        model=Byproductcart
        fields=('id','color_value','size_value','price','item_image','item_id',
        'item_name','quantity','item_url','total_price',)
    def get_color_value(self,obj):
        return obj.product.get_color()
    def get_size_value(self,obj):
        return obj.product.get_size()
    def get_item_image(self,obj):
        return obj.item.get_image_cover()
    def get_price(self,obj):
        return obj.product.price
    def get_item_name(self,obj):
        return obj.item.name
    def get_item_url(self,obj):
        return obj.item.get_absolute_url()
    def get_total_price(self,obj):
        return obj.total_price()

class ByproductcartSerializer(serializers.ModelSerializer):
    color_value = serializers.SerializerMethodField()
    size_value = serializers.SerializerMethodField()
    item_image = serializers.SerializerMethodField()
    item_name = serializers.SerializerMethodField()
    item_url = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    percent_discount_deal=serializers.SerializerMethodField()
    sizes=serializers.SerializerMethodField()
    colors=serializers.SerializerMethodField()
    count_variation=serializers.SerializerMethodField()
    inventory=serializers.SerializerMethodField()
    class Meta:
        model=Byproductcart
        fields=('id','product_id','color_value','size_value','price','item_image','item_id',
        'item_name','quantity','item_url','total_price','colors','inventory',
        'percent_discount_deal','sizes','count_variation',)
    def get_color_value(self,obj):
        return obj.product.get_color()
    def get_size_value(self,obj):
        return obj.product.get_size()
    def get_item_image(self,obj):
        return obj.item.get_image_cover()
    def get_price(self,obj):
        return obj.product.price
    def get_item_name(self,obj):
        return obj.item.name
    def get_item_url(self,obj):
        return obj.item.get_absolute_url()
    def get_total_price(self,obj):
        return obj.total_price()
    def get_colors(self,obj):
        return obj.item.get_color_deal()
    def get_sizes(self,obj):
        return obj.item.get_size_deal()
    def get_percent_discount_deal(self,obj):
        return obj.product.percent_discount_deal_shock
    def get_count_variation(self,obj):
        return obj.item.count_variation()
    def get_inventory(self,obj):
        return obj.product.inventory

class CartitemcartSerializer(serializers.ModelSerializer):
    item_name = serializers.SerializerMethodField()
    item_url=serializers.SerializerMethodField()
    color_value=serializers.SerializerMethodField()
    size_value=serializers.SerializerMethodField()
    item_image=serializers.SerializerMethodField()
    discount_price=serializers.SerializerMethodField()
    total_price=serializers.SerializerMethodField()
    price=serializers.SerializerMethodField()
    byproduct=serializers.SerializerMethodField()
    sizes=serializers.SerializerMethodField()
    colors=serializers.SerializerMethodField()
    shop_name=serializers.SerializerMethodField()
    count_variation=serializers.SerializerMethodField()
    inventory=serializers.SerializerMethodField()
    promotion=serializers.SerializerMethodField()
    shock_deal_type=serializers.SerializerMethodField()
    class Meta:
        model = CartItem
        fields = ('id','item_id','item_name','item_url','product_id',
        'color_value','size_value','quantity','discount_price','item_image',
        'price','total_price','byproduct','colors','sizes','count_variation',
        'promotion','shop_name','check','inventory','shock_deal_type',
        )
    def get_color_value(self,obj):
        return obj.product.get_color()
    def get_size_value(self,obj):
        return obj.product.get_size()
    def get_item_image(self,obj):
        return obj.get_image()
    def get_price(self,obj):
        return obj.product.price
    def get_item_name(self,obj):
        return obj.item.name
    def get_item_url(self,obj):
        return obj.item.get_absolute_url()
    def get_total_price(self,obj):
        return obj.total_discount_cartitem()
    def get_discount_price(self,obj):
        return obj.product.total_discount()
    def get_byproduct(self,obj):
        return ByproductcartSerializer(obj.byproduct.all().filter(item__byproduct__valid_to__gt=datetime.datetime.now()-datetime.timedelta(seconds=10)), many=True).data
    def get_colors(self,obj):
        return obj.item.get_color()
    def get_sizes(self,obj):
        return obj.item.get_size()
    def get_count_variation(self,obj):
        return obj.item.count_variation()
    def get_inventory(self,obj):
        return obj.product.inventory
    def get_promotion(self,obj):
        return obj.item.get_promotion()
    def get_shock_deal_type(self,obj):
        return obj.item.shock_deal_type()
    def get_shop_name(self,obj):
        return obj.shop.name
class CartItemSerializer(serializers.ModelSerializer):
    item_name = serializers.SerializerMethodField()
    item_url=serializers.SerializerMethodField()
    color_value=serializers.SerializerMethodField()
    size_value=serializers.SerializerMethodField()
    item_image=serializers.SerializerMethodField()
    discount_price=serializers.SerializerMethodField()
    total_price=serializers.SerializerMethodField()
    price=serializers.SerializerMethodField()
    byproduct=serializers.SerializerMethodField()
    class Meta:
        model = CartItem
        fields = ('id','item_id','item_name','item_url','product_id',
        'color_value','size_value','quantity','discount_price','item_image',
        'price','total_price','byproduct',
        )
    def get_color_value(self,obj):
        return obj.product.get_color()
    def get_size_value(self,obj):
        return obj.product.get_size()
    def get_item_image(self,obj):
        return obj.get_image()
    def get_price(self,obj):
        return obj.product.price
    def get_item_name(self,obj):
        return obj.item.name
    def get_item_url(self,obj):
        return obj.item.get_absolute_url()
    def get_total_price(self,obj):
        return obj.total_discount_cartitem()
    def get_discount_price(self,obj):
        return obj.product.total_discount()
    def get_byproduct(self,obj):
        return ByproductSerializer(obj.byproduct.all().filter(item__byproduct__valid_to__gt=datetime.datetime.now()-datetime.timedelta(seconds=10)), many=True).data
    