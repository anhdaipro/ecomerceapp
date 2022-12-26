from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import  Q
from django.urls import reverse
from orderactions.models import *
from discounts.models import *
from carts.models import *
import datetime
from django.utils import timezone
from carts.models import *
# Create your models here.

PAYMENT_CHOICES = (
    ('PayPal', 'PayPal'),
    ('Payment on delivery','Payment on delivery')
)
DEFAULT_SHIPPING_ID = 1
class Order(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    items=models.ManyToManyField(to="carts.CartItem",related_name='order_cartitem')
    shop=models.ForeignKey(to="shop.Shop",on_delete=models.CASCADE,related_name='order_shop')
    ordered=models.BooleanField(default=False)
    ref_code = models.CharField(max_length=20)
    payment_number=models.CharField(max_length=20,null=True)
    payment_choice=models.CharField(max_length=20,choices=PAYMENT_CHOICES,default='After')
    ordered_date = models.DateTimeField()
    accepted_date = models.DateTimeField(null=True)
    received_date = models.DateTimeField(null=True)
    canceled_date = models.DateTimeField(null=True)
    shipping_start_date = models.DateTimeField(null=True)
    shipping=models.ForeignKey(to='shipping.Shipping',on_delete=models.SET_NULL,null=True,blank=True,related_name='order_shipping')
    shipping_address = models.ForeignKey(
    'account.Address', related_name='shipping_address', on_delete=models.SET_NULL, blank=True, null=True)
    voucher=models.ForeignKey(to='discounts.Voucher',on_delete=models.SET_NULL,null=True,blank=True,related_name='order_voucher')
    award=models.ForeignKey(to='discounts.Award',on_delete=models.SET_NULL,null=True,blank=True,related_name='order_voucher')
    follower_offer=models.ForeignKey(to='discounts.Follower_offer',on_delete=models.SET_NULL,null=True,blank=True,related_name='order_voucher')
    being_delivered = models.BooleanField(default=False)
    accepted=models.BooleanField(default=False)
    received = models.BooleanField(default=False)
    refund_requested = models.BooleanField(default=False)
    refund_granted = models.BooleanField(default=False)
    canceled=models.BooleanField(default=False)
    amount=models.FloatField(default=0)
    discount_voucher=models.FloatField(default=0,null=True)
    discount_offer=models.FloatField(default=0,null=True)
    
    def __str__(self):
        return str(self.ref_code)
    def get_absolute_url(self):
        return reverse("order", kwargs={"id": self.id})
    
    def get_voucher(self):
        vouchers=Voucher.objects.filter(order_voucher=self,valid_to__gt=timezone.now())
        if vouchers.exists():
            return vouchers.first().id
        
    def get_discount_voucher(self):
        discount_voucher=0
        if self.voucher and self.voucher.valid_to>timezone.now():
            if self.total_discount_order()>=self.voucher.minimum_order_value:
                if self.voucher.discount_type=='1':
                    discount_voucher=self.total_discount_order()*self.voucher.percent/100
                    if self.voucher.maximum_discount and self.total_discount_order()*self.voucher.percent/100> self.voucher.maximum_discount:
                        discount_voucher=self.voucher.maximum_discount
                else:
                    discount_voucher=self.voucher.amount
        return discount_voucher
    
    def discount_product(self):
        total_discount=0
        for order_item in self.items.all():
            total_discount+=order_item.save_main()
        return total_discount
    
    def discount_promotion(self):
        discount_promotion=0
        for order_item in self.items.all():
            discount_promotion+=order_item.discount_promotion()
        return discount_promotion

    def discount_deal(self):
        discount_deal=0
        for order_item in self.items.all():
            if order_item.save_deal():
                discount_deal+=order_item.save_deal()
        return discount_deal
    
    def total_price_order(self):
        total=0
        for order_item in self.items.all():
            total+=order_item.total_price_cartitem()
        return total
    
    def total_discount_order(self):
        total=0
        for order_item in self.items.all():
            total+=order_item.total_discount_cartitem()
        return total

    def fee_shipping(self):
        fee_shipping=0
        if self.shipping:
            if self.shipping.method=="Tiết kiệm":
                fee_shipping=16400
            elif self.shipping.method=="Nhanh":
                fee_shipping=19600
            else: 
                fee_shipping=39600
        return fee_shipping

    def total_final_order(self):
        return self.total_price_order()-self.get_discount_voucher()-self.discount_deal()-self.discount_product()-self.discount_promotion()+self.fee_shipping()

    def count_item_cart(self):
        count_cart=0
        for order_item in self.items.all():
            count_cart += order_item.count_item_cart()
        return count_cart
        
    def count_cartitem(self):
        count_cart=0
        for order_item in self.items.all():
            count_cart += 1
        return count_cart
    
    
ADDRESS_CHOICES = (
    ('B', 'Billing'),
    ('S', 'Shipping'),
)
PAYMENT_CHOICES = (  
    ('P', 'PayPal'), 
)
class Payment(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    amount = models.FloatField()
    payment_number=models.CharField(max_length=30)
    order=models.ManyToManyField(Order,blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    paid=models.BooleanField(default=False)
    payment_method = models.CharField(choices=PAYMENT_CHOICES,max_length=10,default='P')
    def __str__(self):
        return str(self.user)


