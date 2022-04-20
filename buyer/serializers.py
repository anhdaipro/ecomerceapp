from rest_framework import serializers
from shop.models import *
from cart.models import *
from category.models import *
from myweb.models import *
from account.models import *
from django.contrib import auth
from djoser.serializers import UserCreateSerializer
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
class UserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'username', 'password')

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model=Profile
        fields = ('phone',)

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
        Profile.objects.create(user = instance,**profile_data)
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
        filtered_user_by_email = User.objects.filter(email=email)
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

class OrderItemSerializer(serializers.ModelSerializer):
    item = serializers.SerializerMethodField()
    final_price = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
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