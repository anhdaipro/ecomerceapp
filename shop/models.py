from django.db import models
from cloudinary_storage.storage import RawMediaCloudinaryStorage
# Create your models here.
from django.db import models
from functools import reduce
from django.db.models import  Q
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.db.models.expressions import Col
from categories.models import Category
from django.urls import reverse
from django.utils import timezone
from django.db.models import Max, Min, Count, Avg,Sum
from discounts.models import *
from shipping.models import *
from orderactions.models import *
from myweb.models import *
from carts.models import *
from orders.models import *
from categories.models import Category
import datetime
import re
import subprocess
from slugify import slugify
from mimetypes import guess_type
class IpModel(models.Model):
    ip=models.CharField(max_length=100)
    create_at=models.DateTimeField(auto_now=True)
shop_type=(
    ('Mall','Shopmall'),
    ('Favourite','Favourite'),
)
class Shop(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name='shop')
    name = models.CharField(max_length=100,null=True)
    description = models.CharField(max_length=255,null=True)
    create_at=models.DateTimeField(auto_now=True)
    shipping=models.ManyToManyField(to="shipping.Shipping",blank=True)
    shop_type=models.CharField(max_length=25,choices=shop_type,null=True)
    views=models.IntegerField(default=0)
    slug=models.SlugField(null=True)
    description_url=models.ManyToManyField(Image_home,blank=True)
    image_cover=models.ImageField(upload_to='shop/',null=True)
    city=models.CharField(max_length=200,null=True)
    def __str__(self):
        return str(self.user)
    def save(self, *args, **kwargs):
        #this line below give to the instance slug field a slug name
        self.slug = slugify(self.name)
        #this line below save every fields of the model instance
        super(Shop, self).save(*args, **kwargs) 
    def get_image(self):
        if self.image_cover and hasattr(self.image_cover,'url'):
            return self.image_cover.url
    
    def num_follow(self):
        return Follower.objects.filter(shop=self).count()
    def count_product(self):
        return Item.objects.filter(shop=self).count()
    def total_review(self):
        return ReView.objects.filter(cartitem__shop=self).count()
    def averge_review(self):
        avg = 0
        reviews = ReView.objects.filter(cartitem__shop=self).aggregate(
            average=Avg('review_rating'))
        if reviews["average"] is not None:
            avg = float(reviews["average"])
        return avg
    def total_order(self):
        return Order.objects.filter(shop=self,ordered=True).count()

    
class UploadItem(models.Model):
    upload_by=models.ForeignKey(Shop, on_delete=models.CASCADE)
    file=models.FileField(upload_to='item/',storage=RawMediaCloudinaryStorage())
    image_preview=models.FileField(upload_to='item/',null=True,storage=RawMediaCloudinaryStorage())
    duration=models.FloatField(null=True)
    upload_date=models.DateTimeField(auto_now_add=True)
    def get_media(self):
        if self.file and hasattr(self.file,'url'):
            return self.file.url
    def file_preview(self):
        if self.image_preview and hasattr(self.image_preview,'url'):
            return self.image_preview.url
    def media_type(self):
        
        if self.image_preview:
            return "video"
        else:
            return 'image'
status_choice=(
    ('1','New'),
    ('2','Like New'),
)

class Item(models.Model):
    category=models.ForeignKey(Category,on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    brand=models.TextField(max_length=200)
    shop=models.ForeignKey(Shop,on_delete=models.CASCADE)
    media_upload=models.ManyToManyField(UploadItem,blank=True,related_name='media_upload')
    shipping_choice=models.ManyToManyField(to="shipping.Shipping",blank=True,related_name='shipping_choice')
    description=models.TextField(max_length=3000)
    sku_product=models.CharField(max_length=20,null=True)
    status=models.CharField(max_length=20,choices=status_choice,default='1')
    pre_order=models.CharField(max_length=20,null=True)
    weight=models.IntegerField(null=True)
    height=models.IntegerField(null=True)
    width=models.IntegerField(null=True)
    length=models.IntegerField(null=True)
    price_ship=models.FloatField(null=True,blank=True)
    is_active=models.BooleanField(default=False)
    views=models.IntegerField(default=0)
    slug=models.SlugField(max_length=150,null=True)
    violet=models.BooleanField(default=False)
    hidden=models.BooleanField(default=False)
    created=models.DateTimeField(auto_now=True)
    detail=models.JSONField(null=True)
    def __str__(self):
        return str(self.name)
   

    def count_review(self):
        return ReView.objects.filter(cartitem__product__item=self).count()
    def average_review(self):
        # here status = True because in my view i have defined just for those which status is True
        # the aggregate(avarage) --> the word of avarage is up to user
        reviews = ReView.objects.filter(cartitem__product__item=self).aggregate(
            average=Avg('review_rating'))
        avg = 0
        if reviews["average"] is not None:
            avg = float(reviews["average"])
        return avg
    
    def get_size(self):
        size=Size.objects.filter(variation__item=self,variation__inventory__gt=0)
        list_size=[{'id':i.id,'name':i.name,'value':i.value,'variation':[variation.id for variation in i.variation_set.filter(inventory__gt=0)]}for i in size.distinct()]
        return list_size
    def get_deal_choice(self):
        if self.get_deal_shock_current():
            return [variation for variation in self.get_deal_shock_current().variations if variation['enable']][0]
    def get_color(self):
        color=Color.objects.filter(variation__item=self,variation__inventory__gt=0)
        list_color=[{'image':i.get_file(),'id':i.id,'name':i.name,'value':i.value,'variation':[variation.id for variation in i.variation_set.filter(inventory__gt=0)]}for i in color.distinct()]
        return list_color
    def get_variation_choice(self):
        variation=Variation.objects.filter(item=self).first()
        return {'product_id':variation.id,'inventory':variation.inventory,
        'discount_price':variation.get_discount_product(),'price':variation.price,
        'color_value':variation.get_color(),'size_value':variation.get_size()}
    def get_list_color(self):
        colors=Color.objects.filter(variation__item=self).distinct()
        list_color=[{'file':color.get_file(),'file_preview':None,'filetype':'image','id':color.id,'name':color.name,'value':color.value} for color in colors]
        return list_color
    def get_list_size(self):
        sizes=Size.objects.filter(variation__item=self).distinct()
        list_size=[{'id':size.id,'value':size.value,'name':size.name} for size in sizes]
        return list_size
    def get_color_deal(self):
        color=Color.objects.filter(variation__item=self).distinct()
        list_color=[{'id':i.id,'name':i.name,'value':i.value,'variation':[variation.id for variation in i.variation_set.filter(inventory__gt=0)]}for i in color.distinct()]
        return list_color
    def get_size_deal(self):
        size=Size.objects.filter(variation__item=self).distinct()
        list_size=[{'id':i.id,'name':i.name,'value':i.value,'variation':[variation.id for variation in i.variation_set.filter(inventory__gt=0)]}for i in size.distinct()]
        return list_size
    
    def num_like(self):
        return self.item_likers.all().count()
    def avg_price(self):
        variations=Variation.objects.filter(item=self).aggregate(avg=Avg('price'))
        return variations['avg']
    def avg_discount_price(self):
        if self.get_program_current():
            variations=[variation['promotion_price'] for variation in self.get_program_current().variations if variation['enable'] and variation['promotion_stock'] and variation['item_id']==self.id]
            discount=reduce(lambda x, y: x+y,variations)
            return discount/len(variations)
    def avg_discount_price_flash_sale(self):
        if self.get_flash_sale_current():
            variations=[variation['promotion_price'] for variation in self.get_flash_sale_current().variations if variation['enable'] and variation['promotion_stock'] and variation['item_id']==self.id]
            discount=reduce(lambda x, y: x+y,variations)
            return discount/len(variations)
    def get_promotion_stock(self):
        if self.get_flash_sale_current():
            variations=[variation['promotion_stock'] for variation in self.get_flash_sale_current().variations if variation['enable'] and variation['promotion_stock'] and variation['item_id']==self.id]
            stocks=reduce(lambda x, y: x+y,variations)
            return int(stocks/len(variations))
    def get_combo_current(self):
        promotion_combo=Promotion_combo.objects.filter(products=self,valid_from__lt=timezone.now(),valid_to__gt=timezone.now())
        if promotion_combo.exists():
            return promotion_combo.first()
    def number_order_flash_sale(self):
        quantity=0
        if self.get_flash_sale_current():
            flash_sale=self.get_flash_sale_current()
            orders=Order.objects.filter(ordered=True,canceled=False,ordered_date__gte=flash_sale.valid_from,ordered_date__lte=flash_sale.valid_to)
            cartitem=CartItem.objects.filter(order_cartitem__in=orders,item=self).aggregate(sum=Sum('quantity'))
            if cartitem['sum']:
                quantity=cartitem['sum']
        return quantity
    def percent_discount(self):
        percent=0
        if self.get_program_current():
            percent=100-float(self.avg_discount_price())*100/float(self.avg_price())                  
        return percent
    def percent_discount_deal(self):
        percent=0
        if self.get_deal_shock_current():
            percent= (float(self.avg_price())-float(self.avg_discount_price_deal()))*100/float(self.avg_price())
        return percent
    def percent_discount_flash_sale(self):
        percent=0
        if self.get_flash_sale_current():
            percent=100-float(self.avg_discount_price_flash_sale())*100/float(self.avg_price())
        return percent
    def total_inventory(self):
        variations = Variation.objects.filter(item=self).aggregate(sum=Sum('inventory'))
        total_inventory = 0
        if variations['sum'] is not None:
            total_inventory=int(variations["sum"])
        return total_inventory
    
    def percent_discount_total(self):
        percent=0
        if self.get_flash_sale_current():
            percent=self.percent_discount_flash_sale()
        else:
            percent=self.percent_discount()
        return int(percent)
    def max_price(self):
        variations = Variation.objects.filter(item=self).aggregate(max=Max('price'))
        max_price=int(variations["max"])
        return max_price
    
    def count_variation(self):
        count=0
        size=Size.objects.filter(variation__item=self,variation__inventory__gt=0)
        if size.exists():
            count+=1
        color=Color.objects.filter(variation__item=self,variation__inventory__gt=0)
        if color.exists():
            count+=1
        return count
    
    def min_price(self):
        variations = Variation.objects.filter(item=self).aggregate(min=Min('price'))
        min_price=int(variations["min"])
        return min_price
    
    def number_order(self):
        order=Order.objects.filter(items__product__item=self,ordered=True).aggregate(count=Count('id'))
        number_order = int(order['count'])
        return number_order
    
    def get_voucher(self):
        vouchers=Voucher.objects.filter(products=self,valid_from__lt=timezone.now(),valid_to__gt=timezone.now())
        if vouchers.exists():
            return list(vouchers.values())[0]
    
    def shock_deal_type(self):
        if Buy_with_shock_deal.objects.filter(main_products=self,valid_from__lt=timezone.now(),valid_to__gt=timezone.now()).exists():
            return Buy_with_shock_deal.objects.filter(main_products=self,valid_from__lt=timezone.now(),valid_to__gt=timezone.now()).last().shock_deal_type
    
    def shipping(self):
        return Shipping.objects.all().last()

    def get_promotion(self):
        promotion_combo=Promotion_combo.objects.filter(products=self,valid_from__lt=timezone.now(),valid_to__gt=timezone.now())
        if promotion_combo.exists():
            promotion_combo=promotion_combo.first()
            return {'id':promotion_combo.id,'combo_type':promotion_combo.combo_type,
            'quantity_to_reduced':promotion_combo.quantity_to_reduced,
            'limit_order':promotion_combo.limit_order,'discount_percent':promotion_combo.discount_percent,
            'discount_price':promotion_combo.discount_price,
            'price_special_sale':promotion_combo.price_special_sale}
    
    def get_program_current(self):
        shop_program=Shop_program.objects.filter(products=self,valid_from__lt=timezone.now(),valid_to__gt=timezone.now())
        if shop_program.exists():
            return shop_program.first()
    def get_flash_sale_current(self):
        flash_sale=Flash_sale.objects.filter(products=self,valid_from__lt=timezone.now(),valid_to__gt=timezone.now())
        if flash_sale.exists():
            return flash_sale.first()
    def get_deal_shock_current(self):
        deal_shock=Buy_with_shock_deal.objects.filter(byproducts=self,valid_from__lt=timezone.now(),valid_to__gt=timezone.now())
        if deal_shock.exists():
            return deal_shock.first()
    def shock_deal(self):
        deal_shock=Buy_with_shock_deal.objects.filter(main_products=self,valid_from__lt=timezone.now(),valid_to__gt=timezone.now())
        if deal_shock.exists():
            deal_shock=deal_shock.first()
            return {'id':deal_shock.id,
            'limited_product_bundles':deal_shock.limited_product_bundles,
            'minimum_price_to_receive_gift':deal_shock.minimum_price_to_receive_gift,
            'number_gift':deal_shock.number_gift,
            'shock_deal_type':deal_shock.shock_deal_type}
    def check_promotion(self):
        promotion_combo=Promotion_combo.objects.filter(products=self,valid_from__lt=timezone.now(),valid_to__gt=timezone.now())
        if promotion_combo.exists():
            return True

    def get_flash_sale(self):
        flash_sale=Flash_sale.objects.filter(products=self,valid_to__gt=timezone.now()).order_by('valid_to')
        if flash_sale.exists():
            flash_sale=flash_sale.first()
            return {'id':flash_sale.id,'valid_to':flash_sale.valid_to,'valid_from':flash_sale.valid_from}

    def get_media(self):
        return [{'typefile':media.media_type(),'file':media.get_media(),'image_preview':media.file_preview(),'duration':media.duration} for media in self.media_upload.all()]
    
    def get_image_cover(self):
        media_file=[media for media in self.media_upload.all() if media.media_type()=='image'][0].get_media()    
        return media_file

class Liker(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE,related_name='item_likers')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    create_at=models.DateTimeField(auto_now=True)

class BuyMoreDiscount(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE,related_name='buymore_item')
    from_quantity=models.IntegerField()
    to_quantity=models.IntegerField()
    price=models.FloatField()
    def __str__(self):
        return str(self.id)
        
class ShopViews(models.Model):
    shop = models.ForeignKey(
        Shop, related_name="shop_views", on_delete=models.CASCADE
    )
    user=models.ForeignKey(
        User, on_delete=models.CASCADE,null=True
    )
    create_at=models.DateTimeField(auto_now=True)

class ItemViews(models.Model):
    item = models.ForeignKey(
        Item, related_name="item_views", on_delete=models.CASCADE
    )  
    user=models.ForeignKey(
        User, on_delete=models.CASCADE,null=True
    )
    create_at=models.DateTimeField(auto_now=True)

class Color(models.Model):
    name=models.CharField(max_length=20)
    value=models.CharField(max_length=20)
    image=models.ImageField(upload_to='color/',blank=True,null=True)
    def __str__(self):
        return str(self.value)
    
    def get_file(self):
        if self.image and hasattr(self.image,'url'):
            return self.image.url

class Size(models.Model):
    name=models.CharField(max_length=20)
    value=models.CharField(max_length=20)
    def __str__(self):
        return str(self.value)
    

class Variation(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE,related_name='variation_item')
    color=models.ForeignKey(Color, on_delete=models.CASCADE,null=True,blank=True)
    size=models.ForeignKey(Size, on_delete=models.CASCADE,null=True,blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    price=models.IntegerField()
    inventory=models.IntegerField()
    sku_classify=models.CharField(max_length=20,null=True)
    view=models.IntegerField(default=0)
    def __str__(self):
        return str(self.item)
    def get_limit_deal(self):
        if self.item.get_deal_shock_current():
            variations=[variation for variation in self.item.get_deal_shock_current().variations if variation['enable'] and variation['variation_id']==self.id]
            if len(variations)>0:
                return int(variations[0]['user_item_limit'])
    def get_variation_program(self):
        if self.item.get_program_current():
            variations=[variation for variation in self.item.get_program_current().variations if variation['enable'] and variation['variation_id']==self.id]
            if len(variations)>0:
                return int(variations[0]['user_item_limit'])
    def get_limit_flash_sale(self):
        if self.item.get_flash_sale_current():
            variations=[variation for variation in self.item.get_flash_sale_current().variations if variation['enable'] and variation['promotion_stock'] and variation['variation_id']==self.id]
            if len(variations)>0:
                return int(variations[0]['user_item_limit'])
    def get_discount_program(self):
        if self.item.get_program_current():
            variations=[variation for variation in self.item.get_program_current().variations if variation['enable'] and variation['promotion_stock'] and variation['variation_id']==self.id]
            if len(variations)>0:
                return int(variations[0]['promotion_price'])
            
    def get_discount_flash_sale(self):
        if self.item.get_flash_sale_current():
            if self.item.get_flash_sale_current():
                variations=[variation for variation in self.item.get_flash_sale_current().variations if variation['enable'] and variation['promotion_stock'] and variation['variation_id']==self.id]
                if len(variations)>0:
                    return int(variations[0]['promotion_price'])
    def get_discount_product(self):
        if self.get_discount_flash_sale():
            return self.get_discount_flash_sale()
        else:
            return self.get_discount_program()
    def get_discount_deal(self):
        deal_shock=Buy_with_shock_deal.objects.filter(byproducts=self.item,valid_from__lt=timezone.now(),valid_to__gt=timezone.now())
        if deal_shock.exists():
            variations=[variation for variation in deal_shock.first().variations if variation['enable']]
            if len(variations)>0:
                return int(variations[0]['promotion_price'])
    
    def total_discount(self):
        discount=self.price
        if self.get_discount_flash_sale():
            discount=self.get_discount_flash_sale()
        if self.get_discount_program() and self.get_discount_deal():
            return discount-(self.price-self.get_discount_program())-(self.price-self.get_discount_deal())
        if self.get_discount_program():
            discount=self.get_discount_program()
        if self.get_discount_deal():
            discount=self.get_discount_deal()
        return discount

    class Meta:
        ordering=['color']
    def number_order(self):
        number_order=0
        order=Order.objects.filter(items__product=self,received=True).aggregate(count=Count('id'))
        if order['count'] is not None:
            number_order += int(order['count'])
        return number_order
    def get_size(self):
        size=''
        if self.size:
            size=self.size.value
        return size
    def get_color_id(self):
        if self.color:
            return self.color_id
    def get_size_id(self):
        if self.size:
            return self.size_id
    def get_color(self):
        color=''
        if self.color:
            color=self.color.value
        return color
    def get_image(self):
        image=self.item.get_image_cover()
        if self.color:
            if self.color.image:
                image=self.color.image.url
        return image

   
