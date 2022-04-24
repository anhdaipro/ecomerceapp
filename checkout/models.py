from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import  Q
from django.urls import reverse
from actionorder.models import *
from discount.models import *
import datetime
from actionorder.models import *
from django.utils import timezone

from cart.models import *
# Create your models here.

PAYMENT_CHOICES = (
    ('PayPal', 'PayPal'),
    ('Payment on delivery','Payment on delivery')
)
DEFAULT_SHIPPING_ID = 1
class Order(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    items=models.ManyToManyField(OrderItem)
    shop=models.ForeignKey(to="shop.Shop",on_delete=models.CASCADE,related_name='order_shop')
    ordered=models.BooleanField(default=False)
    ref_code = models.CharField(max_length=20,null=True,blank=True)
    payment_number=models.CharField(max_length=20,null=True)
    payment_choice=models.CharField(max_length=20,choices=PAYMENT_CHOICES,default='After')
    ordered_date = models.DateTimeField()
    accepted_date = models.DateTimeField(null=True,blank=True)
    received_date = models.DateTimeField(null=True,blank=True)
    canceled_date = models.DateTimeField(null=True,blank=True)
    shipping_start_date = models.DateTimeField(null=True,blank=True)
    shipping=models.ForeignKey(to='shipping.Shipping',on_delete=models.SET_NULL,null=True,blank=True)
    shipping_address = models.ForeignKey(
    'Address', related_name='shipping_address', on_delete=models.SET_NULL, blank=True, null=True)
    vocher=models.ForeignKey(to='discount.Vocher',on_delete=models.SET_NULL,null=True,blank=True)
    being_delivered = models.BooleanField(default=False)
    accepted=models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    refund_requested = models.BooleanField(default=False)
    refund_granted = models.BooleanField(default=False)
    canceled=models.BooleanField(default=False)
    amount=models.FloatField(null=True,blank=True)
    
    def __str__(self):
        return str(self.ref_code)
    def get_absolute_url(self):
        return reverse("order", kwargs={"id": self.id})

    def get_voucher(self):
        id_voucher=None
        vouchers=Vocher.objects.filter(order=self,valid_to__gt=datetime.datetime.now()-datetime.timedelta(seconds=10))
        if vouchers.exists():
            id_voucher=vouchers.first().id
        return id_voucher
        
    def discount_voucher(self):
        discount_voucher=0
        if self.vocher and self.vocher.valid_to>timezone.now():
            if self.total_discount_order()>=self.vocher.minimum_order_value:
                if self.vocher.discount_type=='1':
                    discount_voucher=self.total_discount_order()*self.vocher.percent/100
                    if self.vocher.maximum_discount and self.total_discount_order()*self.vocher.percent/100> self.vocher.maximum_discount:
                        discount_voucher=self.vocher.maximum_discount
                else:
                    discount_voucher=self.vocher.amount
        return discount_voucher
    
    def discount(self):
        total_discount=0
        for order_item in self.items.all():
            total_discount+=order_item.discount()
        return total_discount

    def discount_promotion(self):
        discount_promotion=0
        for order_item in self.items.all():
            discount_promotion+=order_item.discount_promotion()
        return discount_promotion

    def discount_deal(self):
        discount_deal=0
        for order_item in self.items.all():
            discount_deal+=order_item.discount_deal()
        return discount_deal
    
    def total_price_order(self):
        total=0
        for order_item in self.items.all():
            total+=order_item.total_price_orderitem()
        return total

    def total_discount_order(self):
        return self.total_price_order()-self.discount_deal()-self.discount()

    def fee_shipping(self):
        fee_shipping=0
        if self.shipping:
            fee_shipping=16000
        return fee_shipping

    def total_final_order(self):
        return self.total_price_order()-self.discount_deal()-self.discount()-self.discount_promotion()+self.fee_shipping()

    def count_item_cart(self):
        count_cart=0
        for order_item in self.items.all():
            count_cart += order_item.count_item_cart()
        return count_cart
    def count_orderitem(self):
        count_cart=0
        for order_item in self.items.all():
            count_cart += 1
        return count_cart
    def count_review(self):
        count=0
        for order_item in self.items.all():
            if order_item.review:
                count+=1
        return count
    
ADDRESS_CHOICES = (
    ('B', 'Billing'),
    ('S', 'Shipping'),
)
class Address(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    name=models.CharField(max_length=100)
    address=models.CharField(max_length=100)
    city=models.CharField(max_length=100)
    district=models.CharField(max_length=100,null=True)
    town=models.CharField(max_length=100,null=True)
    phone_number=models.CharField(max_length=20)
    address_choice=models.CharField(max_length=20,null=True)
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES,null=True)
    zip = models.CharField(max_length=100,null=True)
    default = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username
    class Meta:
        verbose_name_plural = 'Addresses'

PAYMENT_CHOICES = (
   
    ('P', 'PayPal'),
   
)
class Payment(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    amount = models.FloatField()
    payment_number=models.CharField(max_length=30,null=True)
    order=models.ManyToManyField(Order,blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    paid=models.BooleanField(default=False)
    payment_method = models.CharField(choices=PAYMENT_CHOICES,max_length=10,default='P')
    def __str__(self):
        return str(self.user)