from rest_framework import serializers
from shop.models import *
from cart.models import *
from category.models import *
from myweb.models import *
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from rest_framework.authtoken.models import Token
from djoser.serializers import UserCreateSerializer
class UserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'password')

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password','token']
        extra_kwargs = {'password': {'write_only': True, 'required': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        Token.objects.create(user=user)
        return user
class CategorySerializer(serializers.ModelSerializer):
    image=serializers.SerializerMethodField()
    class Meta:
        model=Category
        fields=(
            'id',
            'slug',
            'title',
            'image',
        )
    def get_image(self,obj):
        return obj.get_image()
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