class FollowOfferInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model=FollowOffer
        fields=['id','valid_from','valid_to',
        'amount','percent','minimum_order_value','maximum_discount']

class FollowOfferSerializer(FollowOfferInfoSerializer): 
    number_used= serializers.SerializerMethodField()
    count_product=serializers.SerializerMethodField()
    class Meta(FollowOfferInfoSerializer.Meta):
        fields=FollowOfferInfoSerializer.Meta.fields+['voucher_type','maximum_usage','offer_name','number_follower']
    def get_number_used(self,obj):
        return Order.objects.filter(FollowOffer=obj,received=True).count()
    def get_count_product(self,obj):
        return obj.products.all().count()

class FollowOfferdetailSerializer(FollowOfferinfoSerializer): 
    exists=serializers.SerializerMethodField()
    class Meta(FollowOfferinfoSerializer.Meta):
        fields=FollowOfferinfoSerializer.Meta.fields+['discount_type','percent','amount','type_offer']