from discount.models import *
from checkout.models import *
from shop.models import *
from rest_framework import serializers
from djoser.serializers import UserCreateSerializer
class VoucherSerializer(serializers.ModelSerializer):
    number_used= serializers.SerializerMethodField()
    count_product=serializers.SerializerMethodField()
    class Meta:
        model = Vocher
        fields = ['code_type','name_of_the_discount_program','code','valid_from','valid_to',
                'amount','percent','maximum_usage','number_used','count_product']
        read_only_fields = ['code_type']
    def get_number_used(self,obj):
        return Order.objects.filter(vocher=obj,received=True).count()
    def get_count_product(self,obj):
        return obj.product.all().count()

class ComboSerializer(serializers.ModelSerializer):
    list_product=serializers.SerializerMethodField()
    class Meta:
        model = Promotion_combo
        fields = ['promotion_combo_name','from_valid','to_valid','combo_type','list_product'
            'discount_percent','discount_price','price_special_sale','quantity_to_reduced']
    def get_list_product(self,obj):
        return [{'image':item.media_upload.all()[0].upload_file()} for item in obj.product.all()]
       
class VoucherSerializer(serializers.ModelSerializer):
    number_used= serializers.SerializerMethodField()
    count_product=serializers.SerializerMethodField()
    class Meta:
        model = Vocher
        fields = ['code_type','name_of_the_discount_program','code','valid_from','valid_to',
                'amount','percent','maximum_usage','number_used','count_product']
    def get_number_used(self,obj):
        return Order.objects.filter(vocher=obj,received=True).count()
    def get_count_product(self,obj):
        return obj.product.all().count()

        

    