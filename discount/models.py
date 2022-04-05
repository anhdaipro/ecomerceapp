from django.db import models

# Create your models here.
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
class Vocher(models.Model):
    code_type=models.CharField(max_length=10,choices=code_type_choice)
    shop=models.ForeignKey(to='shop.Shop',on_delete=models.CASCADE)
    user=models.ManyToManyField(User,blank=True)
    name_of_the_discount_program=models.CharField(max_length=100)
    code = models.CharField(max_length=5)
    active=models.BooleanField(default=False)
    valid_from=models.DateTimeField()
    valid_to=models.DateTimeField()
    discount_type=models.CharField(max_length=15,choices=type_offer_choice,null=True)
    amount = models.FloatField(null=True)
    percent = models.FloatField(null=True)
    product=models.ManyToManyField(to='shop.Item',blank=True)
    maximum_usage=models.IntegerField(null=True)
    voucher_type=models.CharField(max_length=15,choices=voucher_type_choice)
    minimum_order_value=models.IntegerField(default=0)
    maximum_discount=models.IntegerField(null=True)
    setting_display=models.CharField(max_length=20,choices=setting_display_choice)
    created=models.DateTimeField(auto_now=True)
    

class Shop_program(models.Model):
    shop=models.ForeignKey(to='shop.Shop',on_delete=models.CASCADE)
    name_program=models.CharField(max_length=100)
    product=models.ManyToManyField(to='shop.Item',blank=True)
    from_valid=models.DateTimeField(null=True)
    to_valid=models.DateTimeField(null=True)
    created=models.DateTimeField(auto_now=True)

combo_type_choices=(
('1','percentage discount'),
('2','discount by amount'),
('3','special sale')
)  
class Promotion_combo(models.Model):
    shop=models.ForeignKey(to='shop.Shop',on_delete=models.CASCADE)
    promotion_combo_name=models.CharField(max_length=100)
    product=models.ManyToManyField(to='shop.Item',blank=True)
    from_valid=models.DateTimeField()
    to_valid=models.DateTimeField()
    combo_type=models.CharField(max_length=100,choices=combo_type_choices)
    discount_percent=models.IntegerField(null=True)
    discount_price=models.IntegerField(null=True)
    price_special_sale=models.IntegerField(null=True)
    limit_order=models.IntegerField(default=100)
    quantity_to_reduced=models.IntegerField(default=2)
    created=models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return reverse("promotion_combo", kwargs={"id": self.id})

Shock_Deal_Type=(
    ('1','Buy With Shock Deal'),
    ('2','Buy to receive gifts')
)
class Buy_with_shock_deal(models.Model):
    shop=models.ForeignKey(to='shop.Shop',on_delete=models.CASCADE)
    shock_deal_type=models.CharField(max_length=100,choices=Shock_Deal_Type,default='1')
    program_name_buy_with_shock_deal=models.CharField(max_length=100)
    main_product=models.ManyToManyField(to='shop.Item',related_name='main_product',blank=True)
    byproduct=models.ManyToManyField(to='shop.Item',related_name='byproduct',blank=True)
    from_valid=models.DateTimeField()
    to_valid=models.DateTimeField()
    limited_product_bundles=models.IntegerField(null=True)
    minimum_price_to_receive_gift=models.IntegerField(default=0,null=True)
    number_gift=models.IntegerField(default=0,null=True)
    created=models.DateTimeField(auto_now=True)
class Flash_sale(models.Model):
    shop=models.ForeignKey(to='shop.Shop',on_delete=models.CASCADE)
    product=models.ManyToManyField(to='shop.Item',blank=True)
    from_valid=models.DateTimeField()
    to_valid=models.DateTimeField()
    created=models.DateTimeField(auto_now=True)

class Follower_offer(models.Model):
    shop=models.ForeignKey(to='shop.Shop',on_delete=models.CASCADE)
    user=models.ManyToManyField(User,blank=True)
    offer_name=models.CharField(max_length=100)
    from_valid=models.DateTimeField()
    to_valid=models.DateTimeField()
    type_offer=models.CharField(max_length=100,default='Voucher')
    discount_type=models.CharField(max_length=15,choices=type_offer_choice,null=True)
    amount = models.FloatField(null=True,blank=True)
    percent = models.FloatField(null=True,blank=True)
    voucher_type=models.CharField(max_length=15,choices=voucher_type_choice)
    maximum_discount=models.CharField(max_length=15,choices=maximum_discount_choice)
    max_price=models.IntegerField(null=True)
    minimum_order_value=models.IntegerField(null=True)
    maximum_usage=models.IntegerField(null=True)

class Shop_award(models.Model):
    shop=models.ForeignKey(to='shop.Shop',on_delete=models.CASCADE)
    user=models.ManyToManyField(User,blank=True)
    game_name=models.CharField(max_length=100)
    from_valid=models.DateTimeField()
    to_valid=models.DateTimeField()
    type_voucher=models.CharField(max_length=100,default='Offer')
    discount_type=models.CharField(max_length=15,choices=type_offer_choice,null=True)
    amount = models.FloatField(null=True,blank=True)
    percent = models.FloatField(null=True,blank=True)
    minimum_order_value=models.IntegerField(null=True)
    code_number=models.IntegerField(default=1)
