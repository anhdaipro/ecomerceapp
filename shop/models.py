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
from actionorder.models import *
from cart.models import *
from shipping.models import *
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
    name = models.CharField(max_length=100,null=True)
    description = models.CharField(max_length=255,null=True)
    logo = models.ImageField(upload_to='shop/',null=True)
    create_at=models.DateTimeField(auto_now=True)
    shipping=models.ManyToManyField(to="shipping.Shipping",blank=True)
    shop_type=models.CharField(max_length=25,choices=shop_type,null=True)
    followers = models.ManyToManyField(User, blank=True, related_name='followers')
    view=models.ManyToManyField(IpModel,blank=True)
    slug=models.SlugField(null=True)
    image_cover=models.ImageField(upload_to='shop/',null=True)
    USER_TYPE=(
        ('C','Customer'),
        ('S','Seller')
    )
    GENDER_CHOICE=(
        ('MALE','MALE'),
        ('FEMALE','FEMALE'),
        ('ORTHER','ORTHER')
    )
    user_type=models.CharField(max_length=10,choices=USER_TYPE,blank=True)
    gender=models.CharField(max_length=10,choices=GENDER_CHOICE,blank=True)
    phone_number=models.CharField(max_length=200)
    address=models.CharField(max_length=100)
    zip = models.CharField(max_length=100,blank=True)
    date_of_birth=models.DateField(null=True,blank=True)
    xu=models.IntegerField(default=0,null=True)
    is_online=models.DateTimeField(auto_now=True)
    online=models.BooleanField(default=False)
    def __str__(self):
        return self.user
    def get_absolute_url(self):
        return reverse("category", kwargs={"slug": self.slug})
    def num_follow(self):
        return self.followers.all().count()
    def count_product(self):
        return Item.objects.filter(shop=self).count()
    def total_review(self):
        return ReView.objects.filter(orderitem__shop=self).count()
    def averge_review(self):
        avg = 0
        reviews = ReView.objects.filter(orderitem__shop=self).aggregate(
            average=Avg('review_rating'))
        if reviews["average"] is not None:
            avg = float(reviews["average"])
        return avg
    def total_order(self):
        return Order.objects.filter(shop=self,ordered=True).count()
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
    def  get_absolute_id(self):
        return reverse("vendor:update_item", kwargs={"id": self.id})
    
    def count_review(self):
        return ReView.objects.filter(orderitem__product__item=self).count()
    def average_review(self):
        # here status = True because in my view i have defined just for those which status is True
        # the aggregate(avarage) --> the word of avarage is up to user
        reviews = ReView.objects.filter(orderitem__product__item=self).aggregate(
            average=Avg('review_rating'))
        avg = 0
        if reviews["average"] is not None:
            avg = float(reviews["average"])
        return avg
    def get_size(self):
        list_size=[]
        size=Size.objects.filter(variation__item=self,variation__inventory__gt=0)
        if size.exists():
            list_size=[{'id':i.id,'name':i.name,'value':i.value,'variation':[variation.id for variation in i.variation_set.filter(inventory__gt=0)]}for i in size.distinct()]
        return list_size
    def get_color(self):
        list_color=[]
        color=Color.objects.filter(variation__item=self,variation__inventory__gt=0)
        if color.exists():
            list_color=[{'id':i.id,'name':i.name,'value':i.value,'variation':[variation.id for variation in i.variation_set.filter(inventory__gt=0)]}for i in color.distinct()]
        return list_color
    
    def get_count_deal(self):
        count_deal=0
        if Buy_with_shock_deal.objects.filter(byproduct=self,to_valid__gt=datetime.datetime.now()-datetime.timedelta(seconds=10)).exists():
            deal_valid=Buy_with_shock_deal.objects.filter(byproduct=self,to_valid__gt=datetime.datetime.now()-datetime.timedelta(seconds=10)).first()
            if self in deal_valid.byproduct.all():
                count_deal=Variation.objects.filter(item=self,percent_discount_deal_shock__gt=0).count()
        return count_deal
    def deal_valid(self):
        count_deal=0
        if Buy_with_shock_deal.objects.filter(main_product=self,to_valid__gt=datetime.datetime.now()-datetime.timedelta(seconds=10)).exists():
            count_deal=Buy_with_shock_deal.objects.filter(main_product=self,to_valid__gt=datetime.datetime.now()-datetime.timedelta(seconds=10)).count()
        return count_deal
    def get_color_deal(self):
        list_color=[]
        color=Color.objects.filter(variation__item=self,variation__percent_discount_deal_shock__gt=0)
        if color.exists():
            list_color=[{'id':i.id,'name':i.name,'value':i.value,'variation':[variation.id for variation in i.variation_set.filter(inventory__gt=0)]}for i in color.distinct()]
        return list_color
    def get_size_deal(self):
        list_size=[]
        size=Size.objects.filter(variation__item=self,variation__percent_discount_deal_shock__gt=0)
        if size.exists():
            list_size=[{'id':i.id,'name':i.name,'value':i.value,'variation':[variation.id for variation in i.variation_set.filter(inventory__gt=0)]}for i in size.distinct()]
        return list_size
    def num_like(self):
        return self.liked.all().count()
    def discount_flash_sale(self):
        discount_flash_sale=0
        variations = Variation.objects.filter(item=self).aggregate(max=Max('percent_discount_flash_sale'))
        if variations['max'] is not None:
            discount_flash_sale=int(variations["max"])
        return discount_flash_sale
    def total_inventory(self):
        variations = Variation.objects.filter(item=self).aggregate(sum=Sum('inventory'))
        total_inventory = 0
        if variations['sum'] is not None:
            total_inventory=int(variations["sum"])
        return total_inventory
    def max_price(self):
        max_price=0
        variations = Variation.objects.filter(item=self).aggregate(max=Max('price'))
        if variations['max'] is not None:
            max_price=int(variations["max"])
        return max_price
    
    def percent_discount(self):
        percent=0
        variations = Variation.objects.filter(item=self).aggregate(avg=Avg('percent_discount'))
        if variations['avg'] is not None:
            percent=int(variations['avg'])
        return percent
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
        min_price=0
        variations = Variation.objects.filter(item=self).aggregate(min=Min('price'))
        if variations['min'] is not None:
            min_price=int(variations["min"])
        return min_price
    def number_order(self):
        number_order=0
        order=Order.objects.filter(items__product__item=self,ordered=True).aggregate(count=Count('id'))
        if order['count'] is not None:
            number_order += int(order['count'])
        return number_order
    
    def get_voucher(self):
        list_voucher={}
        voucher_percent=0
        vouchers=Vocher.objects.filter(product=self,valid_to__gt=datetime.datetime.now()-datetime.timedelta(seconds=10))
        if vouchers.exists():
            list_voucher['voucher_info']=list(vouchers.values())
        voucher=Vocher.objects.filter(product=self,valid_to__gt=datetime.datetime.now()-datetime.timedelta(seconds=20)).aggregate(max=Max('percent'))
       
        return list_voucher
    def list_voucher(self):
        voucher=[]
        if Vocher.objects.filter(product=self,valid_to__gte=datetime.datetime.now()-datetime.timedelta(seconds=10)).exists():
            voucher=Vocher.objects.filter(product=self,valid_to__gte=datetime.datetime.now()-datetime.timedelta(seconds=10))
        return voucher
    def shock_deal_type(self):
        if Buy_with_shock_deal.objects.filter(main_product=self,to_valid__gt=datetime.datetime.now()-datetime.timedelta(seconds=10)).exists():
            return Buy_with_shock_deal.objects.filter(main_product=self,to_valid__gt=datetime.datetime.now()-datetime.timedelta(seconds=10)).last().shock_deal_type
    def shipping(self):
        return Shipping.objects.all().last()
    def count_program_valid(self):
        return Shop_program.objects.filter(product=self,to_valid__gt=datetime.datetime.now()-datetime.timedelta(seconds=10)).count()
    def item_info(self):
        info_item={}
        info_item['item_name']=self.name
        info_item['item_id']=self.id
        return info_item
    def get_promotion(self):
        promotion_combo={}
        if Promotion_combo.objects.filter(product=self,to_valid__gt=datetime.datetime.now()-datetime.timedelta(seconds=10)).exists():
            promotion_first=Promotion_combo.objects.filter(product=self,to_valid__gt=datetime.datetime.now()-datetime.timedelta(seconds=10)).first()
            promotion_combo['combo_type']=promotion_first.combo_type
            promotion_combo['id']=promotion_first.id
            promotion_combo['quantity_to_reduced']=promotion_first.quantity_to_reduced
            promotion_combo['combo_url']=promotion_first.get_absolute_url()
            promotion_combo['limit_order']=promotion_first.limit_order
            if promotion_first.combo_type=="1":
                promotion_combo['discount_percent']=promotion_first.discount_percent
            elif promotion_first.combo_type=="2":
                promotion_combo['discount_price']=promotion_first.discount_price
            else:
                promotion_combo['price_special_sale']=promotion_first.price_special_sale
        return promotion_combo
    
    def get_media(self):
        list_media=[]
        for media in self.media_upload.all():
            media_file={}
            media_file['typefile']=media.media_type()
            media_file['file']=media.upload_file()
            media_file['image_preview']=media.file_preview()
            media_file['duration']=media.duration
            list_media.append(media_file)
        return list_media
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
   
