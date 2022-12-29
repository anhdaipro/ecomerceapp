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
    amount_main_products=models.FloatField(null=True,default=0)
    amount_byproducts=models.FloatField(null=True,default=0)
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
    def price_product_main(self):
        return self.product.price
    def get_discount_program_product_main(self):
        discount=0
        if self.get_program_current():
            program=self.get_program_current()
            variations=[variation['promotion_price'] for variation in program.variations if variation['enable'] and variation['promotion_stock']  and variation['variation_id']==self.product_id]
            if len(variations)>0:
                discount=self.price_product_main()-int(variations[0])
        return discount
    def get_discount_flash_sale_product_main(self):
        discount=0
        if self.get_flash_sale_current():
            flash_sale=self.get_flash_sale_current()
            variations=[variation['promotion_price'] for variation in flash_sale.variations if variation['enable'] and variation['promotion_stock']  and variation['variation_id']==self.product_id]
            if len(variations)>0:
                discount=self.price_product_main()- int(variations[0])
        return discount

    def get_deal_shock_current(self):
        if  self.deal_shock and (self.ordered or ( self.deal_shock.valid_to>timezone.now() and self.deal_shock.valid_from<timezone.now())):
            return self.deal_shock
    
    def get_program_current(self):
        if self.program and (self.ordered or (self.program.valid_to>timezone.now() and self.program.valid_from<timezone.now())):
            return self.program
    
    def get_combo_current(self):
        if self.promotion_combo and (self.ordered or ( self.promotion_combo.valid_to>timezone.now() and self.promotion_combo.valid_from<timezone.now())):
            return self.promotion_combo
    
    def get_flash_sale_current(self):
        if self.flash_sale and (self.ordered or ( self.flash_sale.valid_to>timezone.now() and self.flash_sale.valid_from<timezone.now())):
            return self.flash_sale
    
    def total_discount_deal(self):
        total=0
        if self.get_deal_shock_current():
            for byproduct in self.byproduct_cart.all():
                if byproduct.discount_deal_by():
                    total+=byproduct.total_price()
        return total

    def total_price_deal(self):
        total=0
        if self.get_deal_shock_current():
            for byproduct in self.byproduct_cart.all():
                if byproduct.discount_deal_by():
                    total+=byproduct.price_by()
        return total

    def save_deal(self):
        return self.total_price_deal()-self.total_discount_deal()
    
    def get_ref_code(self):
        return Order.objects.filter(items=self).first().ref_code
    
    def discount_promotion(self):
        discount_promotion=0
        discount_price=self.price_product_main()-self.get_discount_product_main()
        if self.get_combo_current():
            promotion_combo=self.get_combo_current()
            quantity_in=self.quantity//promotion_combo.quantity_to_reduced
            quantity_valid=quantity_in*promotion_combo.quantity_to_reduced
            if promotion_combo.combo_type=='1':
                discount_promotion=quantity_valid*discount_price*promotion_combo.discount_percent/100
            if promotion_combo.combo_type=='2':
                discount_promotion=self.quantity*discount_price-quantity_in*promotion_combo.discount_price
            if promotion_combo.combo_type=='3':
                discount_promotion=self.quantity*discount_price-quantity_in*promotion_combo.price_special_sale
        return discount_promotion
   
    def total_price_main(self):
        return self.quantity*self.product.price
    def get_discount_product_main(self):
        discount=0
        if self.get_discount_flash_sale_product_main():
            discount=self.get_discount_flash_sale_product_main()
        if self.get_discount_program_product_main():
            discount=self.get_discount_program_product_main()
        return discount
    def save_main(self):
        return self.quantity*self.get_discount_product_main()
    def total_discount_main(self):
        return self.total_price_main()-self.save_main()
    
    def total_price_cartitem(self):
        total=self.total_price_main()
        if self.deal_shock and self.deal_shock.valid_to>timezone.now() and self.deal_shock.valid_from<timezone.now():
            for byproduct in self.byproduct_cart.all():
                total+=byproduct.price_by()
        return total

    def total_discount_cartitem(self):
        return self.total_price_cartitem()-self.save_deal()-self.discount_promotion()-self.save_main()
    
    
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
        if self.product.get_discount_program():
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