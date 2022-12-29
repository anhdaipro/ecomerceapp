from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
ACTIVE_CHOICE=(
    ('Yes','Yes'),
    ('No','No')
)
# Create your models here.
code_type_choice=(
    ('All','All shop'),
    ('Product','Product')
)
voucher_type_choice=(
     ('Offer','Offer'),
    ('Complete coin','Complete coin')
)
type_offer_choice=(
     ('1','Percent'),
    ('2','Money')
)
maximum_discount_choice=(
    ('L','Limited'),
    ('U','Unlimited')
)
setting_display_choice=(
    ('Show many','Show many places'),
    ('Not public','not public'),
    ('Share','Share througth code vourcher')
)
class Voucher(models.Model):
    code_type=models.CharField(max_length=10,choices=code_type_choice)
    shop=models.ForeignKey(to='shop.Shop',on_delete=models.CASCADE)
    name_of_the_discount_program=models.CharField(max_length=100)
    code = models.CharField(max_length=5)
    active=models.BooleanField(default=False)
    valid_from=models.DateTimeField()
    valid_to=models.DateTimeField()
    discount_type=models.CharField(max_length=15,choices=type_offer_choice,null=True)
    amount = models.FloatField(null=True)
    percent = models.FloatField(null=True)
    products=models.ManyToManyField(to='shop.Item',blank=True,related_name='voucher')
    maximum_usage=models.IntegerField(null=True)
    voucher_type=models.CharField(max_length=15,choices=voucher_type_choice)
    minimum_order_value=models.IntegerField(default=0)
    maximum_discount=models.IntegerField(null=True)
    setting_display=models.CharField(max_length=20,choices=setting_display_choice)
    created=models.DateTimeField(auto_now=True)
    
class Voucheruser(models.Model):
    voucher=models.ForeignKey(to=Voucher,on_delete=models.CASCADE)
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    created=models.DateTimeField(auto_now=True)
class Shop_program(models.Model):
    shop=models.ForeignKey(to='shop.Shop',on_delete=models.CASCADE)
    name_program=models.CharField(max_length=100)
    products=models.ManyToManyField(to='shop.Item',blank=True,related_name='shop_program')
    variations=models.JSONField(null=True)
    valid_from=models.DateTimeField()
    valid_to=models.DateTimeField()
    active=models.BooleanField(default=False)
    created=models.DateTimeField(auto_now=True)
combo_type_choices=(
('1','percentage discount'),
('2','discount by amount'),
('3','special sale')
)  
status=(
    (1,'On'),
    (2,"Off")
)


class Promotion_combo(models.Model):
    shop=models.ForeignKey(to='shop.Shop',on_delete=models.CASCADE)
    promotion_combo_name=models.CharField(max_length=100)
    products=models.ManyToManyField(to='shop.Item',blank=True,related_name='promotion_combo')
    valid_from=models.DateTimeField()
    valid_to=models.DateTimeField()
    combo_type=models.CharField(max_length=100,choices=combo_type_choices)
    discount_percent=models.IntegerField(null=True,blank=True)
    discount_price=models.IntegerField(default=0,null=True,blank=True)
    price_special_sale=models.IntegerField(null=True)
    limit_order=models.IntegerField(default=100)
    quantity_to_reduced=models.IntegerField(default=2)
    created=models.DateTimeField(auto_now=True)

Shock_Deal_Type=(
    ('1','Buy With Shock Deal'),
    ('2','Buy to receive gifts')
)
class Buy_with_shock_deal(models.Model):
    shop=models.ForeignKey(to='shop.Shop',on_delete=models.CASCADE)
    shock_deal_type=models.CharField(max_length=100,choices=Shock_Deal_Type,default='1')
    program_name_buy_with_shock_deal=models.CharField(max_length=100)
    main_products=models.ManyToManyField(to='shop.Item',related_name='main_product',blank=True)
    byproducts=models.ManyToManyField(to='shop.Item',related_name='byproduct',blank=True)
    variations=models.JSONField(null=True)
    valid_from=models.DateTimeField()
    valid_to=models.DateTimeField()
    active=models.BooleanField(default=False)
    limited_product_bundles=models.IntegerField(null=True)
    minimum_price_to_receive_gift=models.IntegerField(default=0,null=True)
    number_gift=models.IntegerField(default=0,null=True)
    
    created=models.DateTimeField(auto_now=True)

    
class Flash_sale(models.Model):
    shop=models.ForeignKey(to='shop.Shop',on_delete=models.CASCADE)
    products=models.ManyToManyField(to='shop.Item',blank=True,related_name='flash_sale')
    variations=models.JSONField(null=True)
    valid_from=models.DateTimeField()
    valid_to=models.DateTimeField()
    active=models.BooleanField(default=False)
    created=models.DateTimeField(auto_now=True)


class Follower_offer(models.Model):
    shop=models.ForeignKey(to='shop.Shop',on_delete=models.CASCADE)
    offer_name=models.CharField(max_length=100)
    valid_from=models.DateTimeField()
    valid_to=models.DateTimeField()
    type_offer=models.CharField(max_length=100,default='Voucher')
    discount_type=models.CharField(max_length=15,choices=type_offer_choice,null=True)
    amount = models.FloatField(null=True,blank=True)
    percent = models.FloatField(null=True,blank=True)
    voucher_type=models.CharField(max_length=15,choices=voucher_type_choice)
    maximum_discount=models.FloatField(null=True)
    minimum_order_value=models.FloatField(null=True,default=0)
    maximum_usage=models.IntegerField(null=True)

class Shop_award(models.Model):
    shop=models.ForeignKey(to='shop.Shop',on_delete=models.CASCADE)
    user=models.ManyToManyField(User,blank=True)
    game_name=models.CharField(max_length=100)
    valid_from=models.DateTimeField()
    valid_to=models.DateTimeField()

class Follower(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='follower')
    shop=models.ForeignKey(to='shop.Shop',on_delete=models.CASCADE)
    follow_offer=models.ForeignKey(Follower_offer,on_delete=models.CASCADE,related_name='follower_offder',null=True)
    created=models.DateTimeField(auto_now=True)
class Award(models.Model):
    shop_award=models.ForeignKey(Shop_award,on_delete=models.CASCADE,related_name='award_shop_award')
    minimum_order_value=models.FloatField()
    type_voucher=models.CharField(max_length=100,default='Offer')
    maximum_discount=models.FloatField(null=True)
    quantity=models.IntegerField()
    amount = models.FloatField(null=True,default=0)
    percent = models.IntegerField(null=True,default=0)
    discount_type=models.CharField(max_length=15,choices=type_offer_choice)
    type_award=models.CharField(max_length=15)
    type_voucher=models.CharField(max_length=15,default="Offer",null=True)

class Gammer(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='gammer')
    shop_award=models.ForeignKey(Shop_award,on_delete=models.CASCADE,related_name='shop_award')
    award=models.ForeignKey(Award,on_delete=models.CASCADE,null=True)
    created=models.DateTimeField(auto_now=True)