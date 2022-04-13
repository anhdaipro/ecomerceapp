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
    def get_number_used(self,obj):
        return Order.objects.filter(vocher=obj,received=True).count()
    def get_count_product(self,obj):
        return obj.product.all().count()

        

    