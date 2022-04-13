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
        fields = ['id','code_type','name_of_the_discount_program','code','valid_from','valid_to',
                'amount','percent','maximum_usage','number_used','count_product','discount_type']
        read_only_fields = ['code_type']
    def get_number_used(self,obj):
        return Order.objects.filter(vocher=obj,received=True).count()
    def get_count_product(self,obj):
        return obj.product.all().count()

class ComboSerializer(serializers.ModelSerializer):
    list_product=serializers.SerializerMethodField()
    class Meta:
        model = Promotion_combo
        fields = ['id','promotion_combo_name','from_valid','to_valid','combo_type','list_product',
            'discount_percent','discount_price','price_special_sale','quantity_to_reduced']
    def get_list_product(self,obj):
        return [{'image':item.media_upload.all()[0].upload_file()} for item in obj.product.all()]
       
class ProgramSerializer(serializers.ModelSerializer):
    list_product=serializers.SerializerMethodField()
    class Meta:
        model = Shop_program
        fields = ['id','name_program','valid_from','valid_to','list_product']

    def get_list_product(self,obj):
        return [{'image':item.media_upload.all()[0].upload_file()} for item in obj.product.all()]

class DealsockSerializer(serializers.ModelSerializer):
    list_mainproduct=serializers.SerializerMethodField()
    list_byproduct=serializers.SerializerMethodField()
    class Meta:
        model = Buy_with_shock_deal
        fields = ['id','shock_deal_type','program_name_buy_with_shock_deal','valid_from','valid_to',
        'list_mainproduct','list_byproduct']
    def get_list_byproduct(self,obj):
        return [{'image':item.media_upload.all()[0].upload_file()} for item in obj.product.all()]
    def get_list_mainproduct(self,obj):
        return [{'image':item.media_upload.all()[0].upload_file()} for item in obj.product.all()]

class FlashsaleSerializer(serializers.ModelSerializer):
    list_product=serializers.SerializerMethodField()
    class Meta:
        model = Flash_sale
        fields = ['id','valid_from','valid_to','list_product']
        
    def get_list_product(self,obj):
        return [{'image':item.media_upload.all()[0].upload_file()} for item in obj.product.all()]

        

    