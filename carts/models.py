from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import  Q
from django.urls import reverse
from discounts.models import *
from orders.models import *
from orderactions.models import *
import datetime
from django.utils import timezone
# Create your models here.
class WhishItem(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    item=models.ForeignKey(to="shop.Item", on_delete=models.CASCADE,related_name='whish_item')
    product=models.ForeignKey(to="shop.Variation", on_delete=models.CASCADE,related_name='whish_product')
    quantity=models.SmallIntegerField(default=1)
    create_at=models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"(self.quantity) of (self.variany)"


class CartItem(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    shop=models.ForeignKey(to="shop.Shop",on_delete=models.CASCADE,related_name='shop_order')
    product=models.ForeignKey(to="shop.Variation", on_delete=models.CASCADE,related_name='cart_product')
    item=models.ForeignKey(to="shop.Item", on_delete=models.CASCADE,related_name='cart_item')
    deal_shock=models.ForeignKey(to="discounts.Buy_with_shock_deal",on_delete=models.SET_NULL, blank=True, null=True)
    promotion_combo=models.ForeignKey(to="discounts.Promotion_combo",on_delete=models.SET_NULL, blank=True, null=True)
    flash_sale=models.ForeignKey(to="discounts.Flash_sale",on_delete=models.SET_NULL, blank=True, null=True)
    program=models.ForeignKey(to="discounts.Shop_program",on_delete=models.SET_NULL, blank=True, null=True)
    quantity=models.SmallIntegerField()
    updated_at = models.DateField(auto_now=True) 
    ordered=models.BooleanField(default=False)
    check=models.BooleanField(default=False)
    class Meta:
        ordering = ['-id']
    def __str__(self):
        return f"{self.quantity}  {self.product.item} of {self.product.item.shop}"
   
    def get_image(self):
        image=self.item.get_image_cover()
        if self.product.color:
            if self.product.color.image:
                image=self.product.color.image.url
        return image
    def get_review(self):
        if self.review_item.all():
            return self.review_item.all().first()
    def count_item_cart(self):
        count=1
        for byproduct in self.byproduct_cart.all():
            if byproduct.item.get_deal_shock_current():
                count+=1
        return count

    def discount_deal(self):
        discount_deal=0
        if self.get_deal_shock_current():
            for byproduct in self.byproduct_cart.all():
                if byproduct.discount_deal_by():
                    discount_deal+=byproduct.discount_deal_by()
        return discount_deal
    def get_ref_code(self):
        return Order.objects.filter(items=self).first().ref_code
    def discount_promotion(self):
        discount_promotion=0
        discount_price=self.product.price
        if self.item.get_program_current() and self.product.get_discount_program():
            discount_price=self.product.get_discount_program()
        if self.item.get_combo_current():
            promotion_combo=Promotion_combo.objects.get(id=self.item.get_combo_current())
            quantity_in=self.quantity//promotion_combo.quantity_to_reduced
            quantity_valid=quantity_in*promotion_combo.quantity_to_reduced
            if promotion_combo.combo_type=='1':
                discount_promotion=quantity_valid*discount_price*promotion_combo.discount_percent/100
            if promotion_combo.combo_type=='2':
                discount_promotion=self.quantity*discount_price-quantity_in*promotion_combo.discount_price
            if promotion_combo.combo_type=='3':
                discount_promotion=self.quantity*discount_price-quantity_in*promotion_combo.price_special_sale
        return discount_promotion
   
    def discount_product(self):
        total_discount=self.discount_main()
        if self.get_deal_shock_current():
            for byproduct in self.byproduct_cart.all():
                if byproduct.discount_by():
                    total_discount+=byproduct.discount_by()
        return total_discount
    def price_main(self):
        return self.quantity*self.product.price

    def discount_main(self):
        discount=0
        if self.product.get_discount_product():
            discount=self.price_main()-self.quantity*self.product.get_discount_product()
        return discount
    
    def total_price_cartitem(self):
        total=0
        total+=self.price_main()
        if self.deal_shock and self.deal_shock.valid_to>timezone.now() and self.deal_shock.valid_from<timezone.now():
            for byproduct in self.byproduct_cart.all():
                total+=byproduct.price_by()
        return total

    def total_discount_cartitem(self):
        return self.total_price_cartitem()-self.discount_deal()-self.discount_promotion()-self.discount_product()
    def get_deal_shock_current(self):
        if self.deal_shock and self.deal_shock.valid_to>timezone.now() and self.deal_shock.valid_from<timezone.now():
            return self.deal_shock.id

class Byproduct(models.Model):
    cartitem=models.ForeignKey(CartItem, on_delete=models.CASCADE,related_name='byproduct_cart')
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    product=models.ForeignKey(to="shop.Variation",on_delete=models.CASCADE,related_name='byproduct_product')
    item = models.ForeignKey(to="shop.Item", on_delete=models.CASCADE,related_name='byproduct_item')
    quantity=models.IntegerField()
    updated_at = models.DateField(auto_now=True)
    def discount_deal_by(self):
        discount=0
        if self.product.get_discount_deal():
            discount= self.price_by()-self.quantity * self.product.get_discount_deal()
        return discount
    def price_by(self):
        return self.quantity*self.product.price
    def discount_by(self):
        discount=0  
        if self.item.get_program_current() and self.product.get_discount_program():
            discount=self.price_by()- self.quantity*self.product.get_discount_program()
        return discount
    def total_price(self):
        return self.price_by()-self.discount_deal_by()-self.discount_by()

    def get_image(self):
        image=self.item.get_image_cover()
        if self.product.color:
            if self.product.color.image:
                image=self.product.color.image.url
        return image