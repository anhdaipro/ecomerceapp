from rest_framework import serializers
from shop.models import *
from carts.models import *
from category.models import *
from myweb.models import *
from account.models import *
from chats.models import *
from itemdetail.models import *
from django.contrib import auth
from djoser.serializers import UserCreateSerializer
from seller.serializers import *
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
class UserorderSerializer(serializers.ModelSerializer):
    avatar=serializers.SerializerMethodField()
    class Meta:
        model=User
        fields=('username','id','avatar',)
    def get_avatar(self,obj):
        return obj.profile.avatar.url
class UserprofileSerializer(UserorderSerializer):
    count_message_unseen=serializers.SerializerMethodField()
    count_notifi_unseen=serializers.SerializerMethodField()
    class Meta(UserorderSerializer.Meta):
        fields = UserorderSerializer.Meta.fields+('count_message_unseen','count_notifi_unseen',)
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

class CategorySerializer(serializers.ModelSerializer):
    url=serializers.SerializerMethodField()
    class Meta:
        model=Category
        fields=('title','url','id',)
    def get_url(self,obj):
        return obj.get_absolute_url()
class CategoryhomeSerializer(CategorySerializer):
    image=serializers.SerializerMethodField()
    class Meta(CategorySerializer.Meta):
        fields=CategorySerializer.Meta.fields+('image',)
    def get_image(self,obj):
        if obj.image:
            return obj.image.url
class CategorydetailSerializer(CategorySerializer):
    image_home= serializers.SerializerMethodField()
    class Meta(CategorySerializer.Meta):
        fields=CategorySerializer.Meta.fields+('image_home',)
    def get_image_home(self,obj):
        image_category=obj.image_category.all()
        return [{'image':i.image.url,'url_field':i.url_field} for i in image_category]

class IteminfoSerializer(serializers.ModelSerializer):
    image=serializers.SerializerMethodField()
    class Meta:
        model = Item
        fields = [
        'id','name','image']
    
    def get_image(self,obj):
        return obj.get_image_cover()

class ByproductSellerSerializer(IteminfoSerializer):
    variations=serializers.SerializerMethodField()
    class Meta(IteminfoSerializer.Meta):
        fields =IteminfoSerializer.Meta.fields + ['variations']
    def get_variations(self,obj):
        return VariationSerializer(obj.variation_item.all(),many=True).data

class ItemSerializer(IteminfoSerializer):
    url=serializers.SerializerMethodField()
    max_price=serializers.SerializerMethodField()
    min_price=serializers.SerializerMethodField()
    percent_discount=serializers.SerializerMethodField()
    class Meta(IteminfoSerializer.Meta):
        fields =IteminfoSerializer.Meta.fields+ [
        'max_price','min_price','url','percent_discount']
    
    def get_url(self,obj):
        return obj.get_absolute_url()
    def get_max_price(self,obj):
        return obj.max_price()
    def get_min_price(self,obj):
        return obj.min_price()
    def get_percent_discount(self,obj):
        return obj.percent_discount_total()

class ItemflasaleSerializer(ItemSerializer):
    percent_discount=serializers.SerializerMethodField()
    number_order=serializers.SerializerMethodField()
    discount_price=serializers.SerializerMethodField()
    promotion_stock=serializers.SerializerMethodField()
    class Meta(ItemSerializer.Meta):
        fields=ItemSerializer.Meta.fields+['number_order','discount_price','promotion_stock']
    def get_percent_discount(self,obj):
        return obj.percent_discount_flash_sale()
    def get_number_order(self,obj):
        return obj.number_order_flash_sale()
    def get_discount_price(self,obj):
        return obj.avg_discount_price_flash_sale()
    def get_promotion_stock(self,obj):
        return obj.get_promotion_stock()
class ItemproductSerializer(IteminfoSerializer):
    class Meta(IteminfoSerializer.Meta):
        fields=IteminfoSerializer.Meta.fields+['sku_product']

field_variation=['variation_id','inventory','color_value','size_value','price','item_id']
class VariationSerializer(serializers.ModelSerializer):
    color_value=serializers.SerializerMethodField()
    size_value=serializers.SerializerMethodField()
    variation_id=serializers.SerializerMethodField()
    class Meta:
        model = Variation
        fields =field_variation
    def get_color_value(self,obj):
        return obj.get_color()
    def get_size_value(self,obj):
        return obj.get_size()
    def get_variation_id(self,obj):
        return obj.id
class VariationsellerSerializer(VariationSerializer):
    number_order=serializers.SerializerMethodField()
    class Meta(VariationSerializer.Meta):
        fields=VariationSerializer.Meta.fields+['id','sku_classify','number_order']
    def get_number_order(self,obj):
        return obj.number_order()
class VariationcartSerializer(serializers.ModelSerializer):
    color_value=serializers.SerializerMethodField()
    size_value=serializers.SerializerMethodField()
    product_id=serializers.SerializerMethodField()
    discount_price=serializers.SerializerMethodField()
    user_item_limit=serializers.SerializerMethodField()
    class Meta:
        model = Variation
        list_file=list(field_variation)
        list_file.remove('variation_id')
        fields =list_file+['product_id','discount_price','user_item_limit']
    def get_color_value(self,obj):
        return obj.get_color()
    def get_size_value(self,obj):
        return obj.get_size()
    def get_product_id(self,obj):
        return obj.id
    def get_user_item_limit(self,obj):
        return obj.get_limit_deal()
    def get_discount_price(self,obj):
        return obj.total_discount()
class ItempageSerializer(ItemSerializer):
    num_like=serializers.SerializerMethodField()
    review_rating=serializers.SerializerMethodField()
    shock_deal_type=serializers.SerializerMethodField()
    promotion=serializers.SerializerMethodField()
    shop_city=serializers.SerializerMethodField()
    voucher=serializers.SerializerMethodField()
    number_order=serializers.SerializerMethodField()
    class Meta(ItemSerializer.Meta):
        fields=ItemSerializer.Meta.fields+['shop_city','brand','voucher',
        'review_rating','num_like','promotion','shock_deal_type','number_order']
    def get_shop_city(self,obj):
        return obj.shop.city
    def get_review_rating(self,obj):
        return obj.average_review()
    def get_num_like(self,obj):
        return obj.num_like()
    def get_promotion(self,obj):
        return obj.get_promotion()
    def get_shock_deal_type(self,obj):
        return obj.shock_deal_type()
    def get_voucher(self,obj):
        return obj.get_voucher()
    def get_number_order(self,obj):
        return obj.number_order()


class ItemSellerSerializer(ItemSerializer):
    total_inventory=serializers.SerializerMethodField()
    number_order=serializers.SerializerMethodField()
    shipping=serializers.SerializerMethodField()
    class Meta(ItemSerializer.Meta):
        my_list=list(ItemSerializer.Meta.fields)
        my_list.remove('percent_discount')
        fields =my_list+ ['number_order','total_inventory','shipping','sku_product']
    def get_total_inventory(self,obj):
        return obj.total_inventory()
    def get_number_order(self,obj):
        return obj.number_order()
    def get_shipping(self,obj):
        return obj.shipping_choice.all()[0].method

class ItemcomboSerializer(ItemSerializer):
    total_inventory=serializers.SerializerMethodField()
    colors=serializers.SerializerMethodField()
    sizes=serializers.SerializerMethodField()
    class Meta(ItemSerializer.Meta):
        fields =ItemSerializer.Meta.fields+ ['colors','sizes','total_inventory']
    def get_total_inventory(self,obj):
        return obj.total_inventory()
    def get_colors(self,obj):
        return obj.get_color()
    def get_sizes(self,obj):
        return obj.get_size()

class ItemdetailSerializer(ItemcomboSerializer):
    category=serializers.SerializerMethodField()
    media_upload=serializers.SerializerMethodField()
    shock_deal_type=serializers.SerializerMethodField()
    promotion=serializers.SerializerMethodField()
    num_like=serializers.SerializerMethodField()
    flash_sale=serializers.SerializerMethodField()
    review_rating=serializers.SerializerMethodField()
    count_review=serializers.SerializerMethodField()
    vouchers=serializers.SerializerMethodField()
    like=serializers.SerializerMethodField()
    user_id=serializers.SerializerMethodField()
    number_order=serializers.SerializerMethodField()
    class Meta(ItemcomboSerializer.Meta):
        fields =ItemcomboSerializer.Meta.fields+ [
            'user_id','category','count_variation','description','media_upload',
            'shock_deal_type','promotion','flash_sale','num_like'
            ,'review_rating','count_review','number_order',
            'vouchers','like','category_id'
        ]
    def get_number_order(self,obj):
        return obj.number_order()
    def get_like(self,obj): 
        request=self.context.get("request")
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        like=False
        if token:
            if request.user in obj.liked.all():
                like=True
        return like
    def get_user_id(self,obj):
        return obj.shop.user_id
    def get_vouchers(self,obj):
        request=self.context.get("request")
        vouchers=Voucher.objects.filter(products=obj,valid_to__gte=datetime.datetime.now()-datetime.timedelta(seconds=10))
        return VoucherdetailSerializer(vouchers,many=True,context={"request": request}).data
    def get_review_rating(self,obj):
        return obj.average_review()
    def get_count_review(self,obj):
        return obj.count_review()
    def get_num_like(self,obj):
        return obj.num_like()
    def get_count_variation(self,obj):
        return obj.count_variation()
    def get_user_id(self,obj):
        return obj.shop.user_id
    def get_flash_sale(self,obj):
        return obj.get_flash_sale()
    def get_category(self,obj):
        return obj.category.get_full_category()
    def get_media_upload(self,obj):
        return obj.get_media()
    def get_promotion(self,obj):
        return obj.get_promotion()
    def get_shock_deal_type(self,obj):
        return obj.shock_deal_type()

class ByproductdealSerializer(ItemSerializer):
    colors=serializers.SerializerMethodField()
    sizes=serializers.SerializerMethodField()
    count_variation=serializers.SerializerMethodField()
    class Meta(ItemSerializer.Meta):
        fields=ItemSerializer.Meta.fields+['colors','sizes','count_variation']
    def get_sizes(self,obj):
        return obj.get_size()
    def get_colors(self,obj):
        return obj.get_color()
    def get_count_variation(self,obj):
        return obj.count_variation()
class ItemdealSerializer(ByproductdealSerializer):
    variation_choice=serializers.SerializerMethodField()
    class Meta(ByproductdealSerializer.Meta):
        fields=ByproductdealSerializer.Meta.fields+['variation_choice']
    def get_variation_choice(self,obj):
        return obj.get_deal_choice()
   
class DealByproductSerializer(serializers.ModelSerializer):
    byproduct=serializers.SerializerMethodField()
    colors_deal=serializers.SerializerMethodField()
    sizes_deal=serializers.SerializerMethodField()
    class Meta:
        model=Buy_with_shock_deal
        fields=('byproduct','sizes_deal','colors_deal','id','limited_product_bundles',
        'minimum_price_to_receive_gift','shock_deal_type')
    def get_byproduct(self,obj):
        listitem=ItemdealSerializer(obj.byproducts.all()[:4],many=True).data
        if obj.limited_product_bundles and obj.limited_product_bundles<4:
            listitem=ItemdealSerializer(obj.byproducts.all()[:obj.limited_product_bundles],many=True).data
        return listitem
    def get_colors_deal(self,obj):
        variations=Variationdeal.objects.filter(deal_shock=obj,enable=True).select_related('variation__color')
        colors=Color.objects.filter(variation__variation_deal__in=variations).distinct()
        return [color.id for color in colors]
    def get_sizes_deal(self,obj):
        variations=Variationdeal.objects.filter(deal_shock=obj,enable=True).select_related('variation__size')
        sizes=Size.objects.filter(variation__variation_deal__in=variations).distinct()
        return [size.id for size in sizes]

class ProductdealSerializer(serializers.ModelSerializer):
    products=serializers.SerializerMethodField()
    class Meta:
        model=Buy_with_shock_deal
        fields=('products','id','shock_deal_type')
    def get_products(self,obj):   
        return ItemSerializer(obj.main_products.all(),many=True).data

class ItemdetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model=Detail_Item
        fields='__all__'

# variation 
class VariationprogramSerializer(serializers.ModelSerializer):
    color_value=serializers.SerializerMethodField()
    size_value=serializers.SerializerMethodField()
    inventory=serializers.SerializerMethodField()
    price=serializers.SerializerMethodField()
    class Meta:
        model=Variation_discount
        fields=field_variation+['enable','id','promotion_price','user_item_limit','promotion_stock']
    def get_color_value(self,obj):
        return obj.variation.get_color()
    def get_size_value(self,obj):
        return obj.variation.get_size()
    def get_inventory(self,obj):
        return obj.variation.inventory
    def get_price(self,obj):
        return obj.variation.price

class VariationflashsaleSerializer(serializers.ModelSerializer):
    color_value=serializers.SerializerMethodField()
    size_value=serializers.SerializerMethodField()
    inventory=serializers.SerializerMethodField()
    price=serializers.SerializerMethodField()
    class Meta:
        model=Variation_discount
        fields=fields=field_variation+['enable','id','promotion_price','user_item_limit','promotion_stock']
    def get_color_value(self,obj):
        return obj.variation.get_color()
    def get_size_value(self,obj):
        return obj.variation.get_size()
    def get_inventory(self,obj):
        return obj.variation.inventory
    def get_price(self,obj):
        return obj.variation.price

class VariationdealSerializer(serializers.ModelSerializer):
    color_value=serializers.SerializerMethodField()
    size_value=serializers.SerializerMethodField()
    inventory=serializers.SerializerMethodField()
    price=serializers.SerializerMethodField()
    class Meta:
        model=Variation_discount
        fields= fields=fields=field_variation+['enable','id','promotion_price','user_item_limit']
    def get_color_value(self,obj):
        return obj.variation.get_color()
    def get_size_value(self,obj):
        return obj.variation.get_size()
    def get_inventory(self,obj):
        return obj.variation.inventory
    def get_price(self,obj):
        return obj.variation.price
#discounts
class VoucherinfoSerializer(serializers.ModelSerializer):
    class Meta:
        model=Voucher
        fields=['id','code_type','code','valid_from','valid_to',
        'discount_type','amount','percent','maximum_usage','voucher_type',
        'minimum_order_value','maximum_discount']

class VoucherSerializer(VoucherinfoSerializer): 
    number_used= serializers.SerializerMethodField()
    count_product=serializers.SerializerMethodField()
    class Meta(VoucherinfoSerializer.Meta):
        fields=VoucherinfoSerializer.Meta.fields+['number_userd','count_product','name_of_the_discount_program']
    def get_number_used(self,obj):
        return Order.objects.filter(voucher=obj,received=True).count()
    def get_count_product(self,obj):
        return obj.products.all().count()

class VoucherdetailSerializer(VoucherinfoSerializer): 
    exists=serializers.SerializerMethodField()
    class Meta(VoucherinfoSerializer.Meta):
        fields=VoucherinfoSerializer.Meta.fields+['exists']
    def get_exists(self,obj):
        request=self.context.get("request")
        if request.user in obj.user.all():
            return True


class VouchersellerSerializer(VoucherinfoSerializer): 
    products=serializers.SerializerMethodField()
    class Meta(VoucherinfoSerializer.Meta):
        fields=VoucherinfoSerializer.Meta.fields+['products','setting_display','name_of_the_discount_program']
    def get_products(self,obj):
        return ItemsellerSerializer(obj.products.all(),many=True).data
class ShopPrograminfoSerializer(serializers.ModelSerializer):
    class Meta:
        model=Shop_program
        fields=['id','valid_to','valid_from','name_program']
class ShopProgramSerializer(ShopPrograminfoSerializer):
    products=serializers.SerializerMethodField()
    class Meta(ShopPrograminfoSerializer.Meta):
        fields=ShopPrograminfoSerializer.Meta.fields+['products']
    def get_products(self,obj):
        return [{'image':item.get_image_cover()} for item in obj.products.all()]
class ShopprogramSellerSerializer(ShopPrograminfoSerializer):
    products=serializers.SerializerMethodField()
    variations=serializers.SerializerMethodField()
    class Meta(ShopPrograminfoSerializer.Meta):
        fields=ShopPrograminfoSerializer.Meta.fields+['products','variations']
    def get_products(self,obj):
        return IteminfoSerializer(obj.products.all(),many=True).data
    def get_variations(self,obj):
        list_variations=Variation_discount.objects.filter(shop_program=obj)
        return VariationprogramSerializer(list_variations,many=True).data
class BuywithsockdealinfoSerializer(serializers.ModelSerializer):
    class Meta:
        model=Buy_with_shock_deal
        fields=['id','shock_deal_type','program_name_buy_with_shock_deal',
        'valid_from','valid_to','limited_product_bundles',
        'minimum_price_to_receive_gift','number_gift']
class BuywithsockdealSerializer(BuywithsockdealinfoSerializer):
    main_products=serializers.SerializerMethodField()
    byproducts=serializers.SerializerMethodField()
    class Meta(BuywithsockdealinfoSerializer.Meta):
        fields=BuywithsockdealinfoSerializer.Meta.fields+['main_products','byproducts']
    def get_byproducts(self,obj):
        return [{'image':item.get_image_cover()} for item in obj.byproducts.all()]
    def get_main_products(self,obj):
        return [{'image':item.get_image_cover()} for item in obj.main_products.all()]

class BuywithsockdealSellerSerializer(BuywithsockdealinfoSerializer):
    main_products=serializers.SerializerMethodField()
    byproducts=serializers.SerializerMethodField()
    variations=serializers.SerializerMethodField()
    class Meta(BuywithsockdealinfoSerializer.Meta):
        fields=BuywithsockdealinfoSerializer.Meta.fields+['main_products','byproducts','variations']
    def get_main_products(self,obj):
        return ItemSellerSerializer(obj.main_products.all(),many=True).data
    def get_byproducts(self,obj):
        return IteminfoSerializer(obj.byproducts.all(),many=True).data
    def get_variations(self,obj):
        list_variations=Variationdeal.objects.filter(deal_shock=obj)
        return VariationdealSerializer(list_variations,many=True).data
    
class ComboinfoSerializer(serializers.ModelSerializer):
    class Meta:
        model=Promotion_combo
        fields=['id','valid_from','valid_to',
        'combo_type','discount_percent','discount_price',
        'price_special_sale','limit_order','quantity_to_reduced']

class ComboSerializer(ComboinfoSerializer):
    products=serializers.SerializerMethodField()
    class Meta(ComboinfoSerializer.Meta):
        fields=(ComboinfoSerializer.Meta.fields)+['promotion_combo_name','products']
    def get_products(self,obj):
        return [{'image':item.get_image_cover()} for item in obj.products.all()]

class ComboItemSerializer(ComboinfoSerializer):
    products=serializers.SerializerMethodField()
    class Meta(ComboinfoSerializer.Meta):
        fields=(ComboinfoSerializer.Meta.fields)+['products']
    def get_products(self,obj):
        return ItemSerializer(obj.products.all()[:6],many=True).data

class CombosellerSerializer(ComboSerializer):
    products=serializers.SerializerMethodField()
    class Meta(ComboSerializer.Meta):
        fields=ComboSerializer.Meta.fields+['promotion_combo_name','products']
    def get_products(self,obj):
        return ItemSellerSerializer(obj.products.all(),many=True).data

class FlashSaleinfoSerializer(serializers.ModelSerializer):
    class Meta:
        model=Flash_sale
        fields=['id','valid_to','valid_from']
class FlashSaleSerializer(FlashSaleinfoSerializer):
    products=serializers.SerializerMethodField()
    class Meta(FlashSaleinfoSerializer.Meta):
        fields=FlashSaleinfoSerializer.Meta.fields+['products']
    def get_products(self,obj):
        return [{'image':item.get_image_cover()} for item in obj.products.all()]
class FlashSaleSellerSerializer(FlashSaleinfoSerializer):
    products=serializers.SerializerMethodField()
    variations=serializers.SerializerMethodField()
    class Meta(FlashSaleinfoSerializer.Meta):
        fields=FlashSaleinfoSerializer.Meta.fields+['products','variations']
    def get_products(self,obj):
        return IteminfoSerializer(obj.products.all(),many=True).data
    def get_variations(self,obj):
        list_variations=Variationflashsale.objects.filter(flash_sale=obj)
        return VariationflashsaleSerializer(list_variations,many=True).data

#discount      
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
    def get_url(self,obj):
        return obj.get_absolute_url()
    def get_avatar(self,obj):
        return obj.user.profile.avatar.url
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

class ShopdetailSerializer(ShopinfoSerializer): 
    count_followings=serializers.SerializerMethodField()
    num_followers=serializers.SerializerMethodField()
    count_product=serializers.SerializerMethodField()
    averge_review=serializers.SerializerMethodField()
    total_review=serializers.SerializerMethodField()
    follow=serializers.SerializerMethodField()
    vouchers=serializers.SerializerMethodField()
    combo=serializers.SerializerMethodField()
    deal=serializers.SerializerMethodField()
    class Meta(ShopinfoSerializer.Meta):
        fields=ShopinfoSerializer.Meta.fields+('create_at','count_followings','vouchers',
        'num_followers','count_product','total_review','averge_review','follow','combo','deal')
    def get_count_followings(self,obj):
        request=self.context.get("request")
        count_follow=Shop.objects.filter(followers=obj.user).count()
        return count_follow
    def get_follow(self,obj):
        request=self.context.get("request")
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        if token:
            user=request.user
            if user in obj.followers.all():
                return True
    def get_num_followers(self,obj):
        return obj.num_follow()
    def get_count_product(self,obj):
        return obj.count_product()
    def get_total_review(self,obj):
        return obj.total_review()
    def get_averge_review(self,obj):
        return obj.averge_review()
    def get_vouchers(self,obj):
        request=self.context.get("request")
        vouchers=Voucher.objects.filter(shop=obj,valid_to__gt=timezone.now(),valid_from__lt=timezone.now())
        return VoucherdetailSerializer(vouchers,many=True,context={"request": request}).data
    def get_deal(self,obj):
        deal_shock=Buy_with_shock_deal.objects.filter(shop=obj,valid_to__gt=timezone.now(),valid_from__lt=timezone.now())
        if deal_shock.exists():
            return True
    def get_combo(self,obj):
        promotion_combo=Promotion_combo.objects.filter(shop=obj,valid_to__gt=timezone.now(),valid_from__lt=timezone.now())
        if promotion_combo.exists():
            return True

class ShoporderSerializer(serializers.ModelSerializer): 
    listvoucher=serializers.SerializerMethodField()
    class Meta:
        model=Shop
        fields=('id','name','listvoucher','user_id',)
    def get_listvoucher(self,obj):
        request=self.context.get("request")
        cartview=CartItem.objects.filter(shop=obj,ordered=False)
        list_voucher=Voucher.objects.filter(products__cart_item__in=cartview).distinct()
        return VoucherdetailSerializer(list_voucher,many=True,context={"request": request}).data
   
class AddressSerializer(serializers.ModelSerializer): 
    class Meta:
        model=Address
        fields = '__all__'

class CartpurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model=CartItem
        fields=('url','item_id','size_value','color_value','image',)

class CartviewSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    url=serializers.SerializerMethodField()
    image=serializers.SerializerMethodField()
    price=serializers.SerializerMethodField()
    promotion=serializers.SerializerMethodField()
    shock_deal_type=serializers.SerializerMethodField()
    class Meta:
        model=CartItem
        fields=('id','item_id','name','image','url',
                'price','shock_deal_type','promotion',)
    
    def get_image(self,obj):
        return obj.get_image()
    def get_name(self,obj):
        return obj.item.name
    def get_url(self,obj):
        return obj.item.get_absolute_url()
    def get_price(self,obj):
        return obj.product.total_discount()
    def get_promotion(self,obj):
        return obj.item.get_promotion()
    def get_shock_deal_type(self,obj):
        return obj.item.shock_deal_type()

class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model=Shop
        fields=('id','name','user_id',)

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
        return obj.get_discount_voucher()
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

class CombodetailseSerializer(ComboinfoSerializer):
    products=serializers.SerializerMethodField()
    class Meta(ComboinfoSerializer.Meta):
        fields=ComboinfoSerializer.Meta.fields + ['products']
    def get_products(self,obj):
        return ItemcomboSerializer(obj.products.all(),many=True).data

class OrderpurchaseSerializer(OrderSerializer):
    shop_url=serializers.SerializerMethodField()
    class Meta(OrderSerializer.Meta):
        fields=OrderSerializer.Meta.fields+(
        'received','canceled','accepted',
        'being_delivered','ordered_date','received_date',
        'canceled_date','accepted_date','shop_url',)
    def get_shop_url(self,obj):
        return obj.shop.get_absolute_url()

class OrderdetailSerializer(OrderpurchaseSerializer):
    address=serializers.SerializerMethodField()
    class Meta(OrderpurchaseSerializer.Meta):
        fields=OrderpurchaseSerializer.Meta.fields+('address',)
    def get_address(self,obj):
        return AddressSerializer(obj.shipping_address).data

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
field_review=['id','review_text','created','name','color_value',
        'size_value','info_more','review_rating','image']
class ReviewSerializer(serializers.ModelSerializer):
    color_value = serializers.SerializerMethodField()
    size_value = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    list_file=serializers.SerializerMethodField()
    rating_bab_category=serializers.SerializerMethodField()
    class Meta:
        model=ReView
        fields=field_review+['anonymous_review','list_file','url','rating_bab_category',
        'edited']
    def get_list_file(self,obj):
        return MediareviewSerializer(obj.media_review.all(),many=True).data  
    def get_color_value(self,obj):
        return obj.cartitem.product.get_color()
    def get_rating_bab_category(self,obj):
        return [obj.rating_product,obj.rating_seller_service,obj.rating_shipping_service]
    def get_size_value(self,obj):
        return obj.cartitem.product.get_size()
    def get_image(self,obj):
        return obj.cartitem.get_image()
    def get_name(self,obj):
        return obj.cartitem.item.name
    def get_url(self,obj):
        return obj.cartitem.item.get_absolute_url()
class ReviewshopSerializer(ReviewSerializer):
    user = serializers.SerializerMethodField()
    reply = serializers.SerializerMethodField()
    ref_code = serializers.SerializerMethodField()
    class Meta(ReviewSerializer.Meta):
        listfiels=list(ReviewSerializer.Meta.fields)
        listfiels.remove('list_file')
        listfiels.remove('rating_bab_category')
        fields=listfiels+['user','reply','ref_code']
    def get_user(self,obj):
        return UserorderSerializer(obj.user).data
    def get_reply(self,obj):
        return obj.get_reply()
    def get_ref_code(self,obj):
        return obj.cartitem.get_ref_code()
    
class ByproductSerializer(serializers.ModelSerializer):
    color_value = serializers.SerializerMethodField()
    size_value = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    class Meta:
        model=Byproduct
        fields=('id','color_value','size_value','price','image','item_id',
        'name','quantity','url','total_price',)
    def get_color_value(self,obj):
        return obj.product.get_color()
    def get_size_value(self,obj):
        return obj.product.get_size()
    def get_image(self,obj):
        return obj.item.get_image_cover()
    def get_price(self,obj):
        return obj.product.price
    def get_name(self,obj):
        return obj.item.name
    def get_url(self,obj):
        return obj.item.get_absolute_url()
    def get_total_price(self,obj):
        return obj.total_price()

class ByproductcartSerializer(ByproductSerializer):
    discount_price=serializers.SerializerMethodField()
    sizes=serializers.SerializerMethodField()
    colors=serializers.SerializerMethodField()
    count_variation=serializers.SerializerMethodField()
    inventory=serializers.SerializerMethodField()
    class Meta(ByproductSerializer.Meta):
        fields=ByproductSerializer.Meta.fields + ('colors','inventory','product_id',
        'discount_price','sizes','count_variation',)
    def get_colors(self,obj):
        return obj.item.get_color()
    def get_sizes(self,obj):
        return obj.item.get_size()
    def get_discount_price(self,obj):
        return obj.product.total_discount()
    def get_count_variation(self,obj):
        return obj.item.count_variation()
    def get_inventory(self,obj):
        return obj.product.inventory

class CartItemSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    url=serializers.SerializerMethodField()
    color_value=serializers.SerializerMethodField()
    size_value=serializers.SerializerMethodField()
    image=serializers.SerializerMethodField()
    discount_price=serializers.SerializerMethodField()
    total_price=serializers.SerializerMethodField()
    price=serializers.SerializerMethodField()
    byproducts=serializers.SerializerMethodField()
    class Meta:
        model = CartItem
        fields = ('id','item_id','name','url','product_id',
        'color_value','size_value','quantity','discount_price','image',
        'price','total_price','byproducts',
        )
    def get_color_value(self,obj):
        return obj.product.get_color()
    def get_size_value(self,obj):
        return obj.product.get_size()
    def get_image(self,obj):
        return obj.get_image()
    def get_price(self,obj):
        return obj.product.price
    def get_name(self,obj):
        return obj.item.name
    def get_url(self,obj):
        return obj.item.get_absolute_url()
    def get_total_price(self,obj):
        return obj.discount_main()
    def get_discount_price(self,obj):
        return obj.product.discount_product()
    def get_byproducts(self,obj):
        list_byproduct=[]
        if obj.item.shock_deal():
            list_byproduct=ByproductSerializer(obj.byproduct_cart.all(), many=True).data
        return list_byproduct
class CartitemcartSerializer(CartItemSerializer):
    sizes=serializers.SerializerMethodField()
    colors=serializers.SerializerMethodField()
    count_variation=serializers.SerializerMethodField()
    inventory=serializers.SerializerMethodField()
    promotion=serializers.SerializerMethodField()
    shock_deal=serializers.SerializerMethodField()
    class Meta(CartItemSerializer.Meta):
        fields = CartItemSerializer.Meta.fields + ('colors','sizes','count_variation',
        'promotion','shop_id','check','inventory','shock_deal',)
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
    def get_shock_deal(self,obj):
        return obj.item.shock_deal()
    def get_byproducts(self,obj):
        list_byproduct=[]
        if obj.item.shock_deal():
            list_byproduct=ByproductcartSerializer(obj.byproduct_cart.all(), many=True).data
        return list_byproduct
class OrdersellerSerializer(OrderSerializer):
    user=serializers.SerializerMethodField()
    class Meta(OrderSerializer.Meta):
        my_list = list(OrderSerializer.Meta.fields)
        my_list.remove('shop')
        my_tuple = tuple(my_list)
        fields=my_tuple+('user',)
    def get_user(self,obj):
        return UserorderSerializer(obj.user).data
