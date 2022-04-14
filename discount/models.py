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
    
