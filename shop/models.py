from django.db import models

# Create your models here.
from django.db import models
from django.db.models import  Q
# Create your models here.
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.db.models.expressions import Col
from category.models import Category
from django.urls import reverse
from django.utils import timezone
from django.db.models import Max, Min, Count, Avg,Sum
from seller.models import *
import datetime
import re
import subprocess
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
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255,null=True)
    address=models.CharField(max_length=255)
    city=models.CharField(max_length=255)
    logo = models.ImageField(upload_to='shop/')
    create_at=models.DateTimeField(auto_now=True)
    shipping=models.ManyToManyField(to="shipping.Shipping",blank=True)
    shop_type=models.CharField(max_length=25,choices=shop_type,null=True)
    followers = models.ManyToManyField(User, blank=True, related_name='followers')
    view=models.ManyToManyField(IpModel,blank=True)
    slug=models.SlugField()
    
    def __str__(self):
        return self.name
      
class Buy_more_discount(models.Model):
    from_quantity=models.IntegerField()
    to_quantity=models.IntegerField()
    price=models.IntegerField()
    def __str__(self):
        return str(self.id)
class UploadItem(models.Model):
    upload_by=models.ForeignKey(Shop, on_delete=models.CASCADE)
    file=models.FileField(upload_to='item/')
    image_preview=models.FileField(upload_to='item/',null=True)
    duration=models.FloatField(null=True)
    upload_date=models.DateTimeField(auto_now_add=True)
    def upload_file(self):
        if self.file and hasattr(self.file,'url'):
            return self.file.url
    def file_preview(self):
        if self.image_preview and hasattr(self.image_preview,'url'):
            return self.image_preview.url
    def media_type(self):
        type_tuple = guess_type(self.file.url, strict=True)
        if (type_tuple[0]).__contains__("image"):
            return "image"
        elif (type_tuple[0]).__contains__("video"):
            return "video"
        else:
            return 'pdf'
status_choice=(
    ('1','New'),
    ('2','Like New'),
)
class Item(models.Model):
    category=models.ForeignKey(Category,on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    brand=models.TextField(max_length=200)
    shop=models.ForeignKey(Shop,on_delete=models.CASCADE)
    media_upload=models.ManyToManyField(UploadItem,blank=True)
    shipping_choice=models.ManyToManyField(to="shipping.Shipping",blank=True,related_name='shipping_choice')
    description=models.TextField(max_length=3000)
    buy_more_discount=models.ManyToManyField(Buy_more_discount,blank=True)
    quantity_limit=models.IntegerField(null=True)#shop_program
    quantity_limit_flash_sale=models.IntegerField(null=True)
    sku_product=models.CharField(max_length=20,null=True)
    status=models.CharField(max_length=20,choices=status_choice,default='1')
    pre_order=models.CharField(max_length=10,null=True)
    weight=models.IntegerField(null=True)
    height=models.IntegerField(null=True)
    width=models.IntegerField(null=True)
    length=models.IntegerField(null=True)
    price_ship=models.FloatField(null=True,blank=True)
    is_active=models.BooleanField(default=False)
    view=models.ManyToManyField(IpModel,blank=True)
    slug=models.CharField(unique=True,max_length=100)
    created=models.DateTimeField(auto_now=True)
    liked=models.ManyToManyField(User,blank=True)
    def __str__(self):
        return str(self.name)
    def save(self, *args, **kwargs):
        super(Item, self).save(*args, **kwargs)
        self.slug = re.sub('[,./\ ]', "-",self.name) + '.' + str(self.id)
    def get_absolute_url(self):
        return reverse("category", kwargs={"slug": self.slug})
   
    
    
class Color(models.Model):
    name=models.CharField(max_length=20)
    value=models.CharField(max_length=20)
    image=models.ImageField(upload_to='color/',blank=True,null=True)
    def __str__(self):
        return str(self.value)
    class Meta:
        ordering=['value']

class Size(models.Model):
    name=models.CharField(max_length=20)
    value=models.CharField(max_length=20)
    def __str__(self):
        return str(self.value)
    class Meta:
        ordering=['value']

class Variation(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    color=models.ForeignKey(Color, on_delete=models.CASCADE,null=True,blank=True)
    size=models.ForeignKey(Size, on_delete=models.CASCADE,null=True,blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    price=models.IntegerField()
    number_of_promotional_products=models.IntegerField(default=0)#shop_program
    percent_discount=models.IntegerField(default=0,null=True)#shop_program
    inventory=models.IntegerField()
    sku_classify=models.CharField(max_length=20,null=True)
    limited_product_bundles=models.IntegerField(null=True)#Buy_with_shock_deal
    percent_discount_deal_shock=models.IntegerField(null=True)#Buy_with_shock_deal
    percent_discount_flash_sale=models.IntegerField(null=True)#flash_sale
    quantity_flash_sale_products=models.IntegerField(null=True)#flash_sale
    def __str__(self):
        return str(self.item)
    def get_absolute_url(self):
        return reverse("deal_shock", kwargs={"id": self.id})
    
    
    
class Byproductcart(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    byproduct=models.ForeignKey(Variation,on_delete=models.CASCADE,null=True)
    quantity=models.IntegerField()
   
