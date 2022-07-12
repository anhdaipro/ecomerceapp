from rest_framework import serializers
from shop.models import *
from carts.models import *
from category.models import *
from myweb.models import *
from account.models import *
from chats.models import *
from django.contrib import auth
from djoser.serializers import UserCreateSerializer
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
class Verifyemailuser(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password','verifyemail']
        extra_kwargs = {
            'password': {'write_only': True}
        }
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
class LoginSerializer(serializers.ModelSerializer):
    tokens = serializers.SerializerMethodField()
    def get_tokens(self, obj):
        user = User.objects.get(email=obj['email'])

        return {
            'refresh': user.tokens()['refresh'],
            'access': user.tokens()['access']
        }

    class Meta:
        model = User
        fields = ['email', 'password', 'username', 'tokens']

    def validate(self, attrs):
        email = attrs.get('email', '')
        password = attrs.get('password', '')
        password = attrs.get('username', '')
        filtered_user_by_email = User.objects.filter(email=email)
        filtered_user_by_username = User.objects.filter(username=username)
        user = auth.authenticate(email=email, password=password)

        return {
            'email': user.email,
            'username': user.username,
            'tokens': user.tokens
        }

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model=Category
        fields=(
            'title',
        )

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
        
class Image_homeSerializer(serializers.ModelSerializer):
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
            'min_price'
        )
    
    def get_image(self,obj):
        return obj.item.get_image_cover()
    def get_max_price(self,obj):
        return obj.item.max_price()
    def get_min_price(self,obj):
        return obj.item.min_price()
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
    shop=serializers.SerializerMethodField()
    percent_discount = serializers.SerializerMethodField()
    category=serializers.SerializerMethodField()
    list_media=serializers.SerializerMethodField()
    list_voucher=serializers.SerializerMethodField()
    count_program_valid=serializers.SerializerMethodField()
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
            'count_program_valid',
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
    def get_count_program_valid(self,obj):
        return obj.count_program_valid()
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

class CartItemSerializer(serializers.ModelSerializer):
    item = serializers.SerializerMethodField()
    final_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = (
            'id',
            'item_name',
            'quantity',
            'final_price'
        )

    def get_item(self, obj):
        return ItemSerializer(obj.item).data

    def get_final_price(self, obj):
        return obj.get_final_price()