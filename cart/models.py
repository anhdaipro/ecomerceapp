from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import  Q
from django.urls import reverse
from actionorder.models import *
from promotions.models import *
import datetime
from django.utils import timezone
# Create your models here.
class WhishItem(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    product=models.ForeignKey(to="shop.Variation", on_delete=models.CASCADE)
    quantity=models.SmallIntegerField(default=1)
    create_at=models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"(self.quantity) of (self.variany)"

class OrderItem(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    shop=models.ForeignKey(to="shop.Shop",on_delete=models.CASCADE,related_name='shop_order')
    product=models.ForeignKey(to="shop.Variation", on_delete=models.CASCADE)
    byproduct=models.ManyToManyField(to="shop.Byproductcart",blank=True)
    deal_shock=models.ForeignKey(to="promotions.Buy_with_shock_deal",on_delete=models.SET_NULL, blank=True, null=True)
    promotion_combo=models.ForeignKey(to="promotions.Promotion_combo",on_delete=models.SET_NULL, blank=True, null=True)
    flash_sale=models.ForeignKey(to="promotions.Flash_sale",on_delete=models.SET_NULL, blank=True, null=True)
    quantity=models.SmallIntegerField()
    updated_at = models.DateField(auto_now=True) 
    ordered=models.BooleanField(default=False)
    check=models.BooleanField(default=False)
    def __str__(self):
        return f"{self.quantity}  {self.product.item} of {self.product.item.shop}"
    def count_item_cart(self):
        count=1
        for byproduct in self.byproduct.all():
            if byproduct.byproduct.item.get_count_deal()>0:
                count+=1
        return count

    def discount_deal(self):
        discount_deal=0
        if self.deal_shock and self.deal_shock.to_valid>timezone.now():
            for byproduct in self.byproduct.all():
                discount_deal+=byproduct.discount_deal_by()
        return discount_deal

    def discount_promotion(self):
        discount_promotion=0
        discount_price=self.product.price
        if self.product.percent_discount and self.product.item.count_program_valid()>0:
            discount_price=self.product.price*(100-self.product.percent_discount)/100
        if self.promotion_combo and self.promotion_combo.to_valid>timezone.now():
            quantity_in=self.quantity//self.promotion_combo.quantity_to_reduced
            quantity_valid=quantity_in*self.promotion_combo.quantity_to_reduced
            if self.promotion_combo.combo_type=='1':
                discount_promotion=quantity_valid*discount_price*self.promotion_combo.discount_percent/100
            if self.promotion_combo.combo_type=='2':
                discount_promotion=self.quantity*discount_price-quantity_in*self.promotion_combo.discount_price
            if self.promotion_combo.combo_type=='3':
                discount_promotion=self.quantity*discount_price-quantity_in*self.promotion_combo.price_special_sale
        return discount_promotion
    def discount(self):
        total_discount=0
        if self.product.percent_discount and self.product.item.count_program_valid()>0:
            total_discount+=self.quantity*self.product.price*(self.product.percent_discount/100)
        if self.deal_shock and self.deal_shock.to_valid>timezone.now():
            for byproduct in self.byproduct.all():
                if byproduct.byproduct.item.count_program_valid()>0:
                    total_discount+=byproduct.discount_by()
                else:
                    total_discount+=0
        return total_discount
    def price_main(self):
        return self.quantity*self.product.price
    def discount_main(self):
        total_discount=0
        if self.product.percent_discount and self.product.item.count_program_valid()>0:
            total_discount=self.quantity*self.product.price*(self.product.percent_discount/100)
        return total_discount
    def total_discount_orderitem(self):
        return self.price_main()-self.discount_main()

    def total_price_orderitem(self):
        total=0
        total+=self.quantity*self.product.price
        if self.deal_shock and self.deal_shock.to_valid>timezone.now():
            for byproduct in self.byproduct.all():
                total+=byproduct.price_by()
        return total