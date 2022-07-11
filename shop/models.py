from django.db import models
from cloudinary_storage.storage import RawMediaCloudinaryStorage
# Create your models here.
from django.db import models
from django.db.models import  Q
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
from django.db.models.expressions import Col
from category.models import Category
from django.urls import reverse
from django.utils import timezone
from django.db.models import Max, Min, Count, Avg,Sum
from discount.models import *
from shipping.models import *
from actionorder.models import *
from myweb.models import *
from cart.models import *
from checkout.models import *
from category.models import Category
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
    create_at=models.DateTimeField(auto_now=True)
    shipping=models.ManyToManyField(to="shipping.Shipping",blank=True)
    shop_type=models.CharField(max_length=25,choices=shop_type,null=True)
    followers = models.ManyToManyField(User, blank=True, related_name='followers')
    views=models.IntegerField(default=0)
    slug=models.SlugField(null=True)
    description_url=models.ManyToManyField(Image_home,blank=True)
    image_cover=models.ImageField(upload_to='shop/',null=True)
    city=models.CharField(max_length=200,null=True)
    def __str__(self):
        return str(self.user)
    def get_image(self):
        if self.image_cover and hasattr(self.image_cover,'url'):
            return self.image_cover.url
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
    file=models.FileField(upload_to='item/',storage=RawMediaCloudinaryStorage())
    image_preview=models.FileField(upload_to='item/',null=True,storage=RawMediaCloudinaryStorage())
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
    name = models.CharField(max_length=120)
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
    pre_order=models.CharField(max_length=20,null=True)
    weight=models.IntegerField(null=True)
    height=models.IntegerField(null=True)
    width=models.IntegerField(null=True)
    length=models.IntegerField(null=True)
    price_ship=models.FloatField(null=True,blank=True)
    is_active=models.BooleanField(default=False)
    views=models.IntegerField(default=0)
    slug=models.CharField(max_length=150)
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
    def update_result(self):
        Item.objects.all().update(slug=re.sub('---', "-",self.name) + '.' + str(self.id))
        # At this point obj.val is still 1, but the value in the database
        # was updated to 2. The object's updated value needs to be reloaded
        # from the database.
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
        size=Size.objects.filter(variation__item=self,variation__inventory__gt=0)
        list_size=[{'id':i.id,'name':i.name,'value':i.value,'variation':[variation.id for variation in i.variation_set.filter(inventory__gt=0)]}for i in size.distinct()]
        return list_size
    
    def get_color(self):
        color=Color.objects.filter(variation__item=self,variation__inventory__gt=0)
        list_color=[{'image':i.image.url,'id':i.id,'name':i.name,'value':i.value,'variation':[variation.id for variation in i.variation_set.filter(inventory__gt=0)]}for i in color.distinct()]
        return list_color
    
    def get_list_color(self):
        color=Color.objects.filter(variation__item=self)
        list_color=[{'file':i.get_file(),'file_preview':None,'filetype':'image','id':i.id,'name':i.name,'value':i.value} for i in color.distinct()]
        return list_color
    
    def get_count_deal(self):
        count_deal=0
        if Buy_with_shock_deal.objects.filter(byproduct=self,valid_to__gt=datetime.datetime.now()-datetime.timedelta(seconds=10)).exists():
            deal_valid=Buy_with_shock_deal.objects.filter(byproduct=self,valid_to__gt=datetime.datetime.now()-datetime.timedelta(seconds=10)).first()
            if self in deal_valid.byproduct.all():
                count_deal=Variation.objects.filter(item=self,percent_discount_deal_shock__gt=0).count()
        return count_deal
    
    def deal_valid(self):
        count_deal=0
        if Buy_with_shock_deal.objects.filter(main_product=self,valid_to__gt=datetime.datetime.now()-datetime.timedelta(seconds=10)).exists():
            count_deal=Buy_with_shock_deal.objects.filter(main_product=self,valid_to__gt=datetime.datetime.now()-datetime.timedelta(seconds=10)).count()
        return count_deal
    
    def get_color_deal(self):
        color=Color.objects.filter(variation__item=self,variation__percent_discount_deal_shock__gt=0)
        list_color=[{'id':i.id,'name':i.name,'value':i.value,'variation':[variation.id for variation in i.variation_set.filter(inventory__gt=0)]}for i in color.distinct()]
        return list_color
    
    def get_size_deal(self):
        size=Size.objects.filter(variation__item=self,variation__percent_discount_deal_shock__gt=0)
        list_size=[{'id':i.id,'name':i.name,'value':i.value,'variation':[variation.id for variation in i.variation_set.filter(inventory__gt=0)]}for i in size.distinct()]
        return list_size
    
    def num_like(self):
        return self.liked.all().count()
    
    def discount_deal(self):
        discount=0
        variations = Variation.objects.filter(item=self,percent_discount_deal_shock__gt=0).aggregate(avg=Avg('percent_discount_deal_shock'))
        if variations['avg'] is not None:
            discount=int(variations["avg"])
        return discount
    
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
        vouchers=Vocher.objects.filter(product=self,valid_to__gt=datetime.datetime.now()-datetime.timedelta(seconds=10))
        if vouchers.exists():
            return list(vouchers.values())[0]

    def list_voucher(self):
        voucher=Vocher.objects.filter(product=self,valid_to__gte=datetime.datetime.now()-datetime.timedelta(seconds=10))
        return voucher

    def shock_deal_type(self):
        if Buy_with_shock_deal.objects.filter(main_product=self,valid_to__gt=datetime.datetime.now()-datetime.timedelta(seconds=10)).exists():
            return Buy_with_shock_deal.objects.filter(main_product=self,valid_to__gt=datetime.datetime.now()-datetime.timedelta(seconds=10)).last().shock_deal_type
    
    def shipping(self):
        return Shipping.objects.all().last()
    def count_program_valid(self):
        return Shop_program.objects.filter(product=self,valid_to__gt=datetime.datetime.now()-datetime.timedelta(seconds=10)).count()
    
    def get_promotion(self):
        promotion_combo=Promotion_combo.objects.filter(product=self,valid_to__gt=datetime.datetime.now()-datetime.timedelta(seconds=10))
        if promotion_combo.exists():
            promotion_combo=promotion_combo.first()
            return {'id':promotion_combo.id,'combo_type':promotion_combo.combo_type,
            'quantity_to_reduced':promotion_combo.quantity_to_reduced,
            'limit_order':promotion_combo.limit_order,'discount_percent':promotion_combo.discount_percent,
            'discount_price':promotion_combo.discount_price,
            'price_special_sale':promotion_combo.price_special_sale}
    
    def get_media(self):
        return [{'typefile':media.media_type,'file':media.upload_file(),'image_preview':media.file_preview(),'duration':media.duration} for media in self.media_upload.all()]
    
    def get_image_cover(self):
        media_file=[media for media in self.media_upload.all() if media.media_type()=='image'][0].upload_file()    
        return media_file

    def percent_discount(self):
        percent=0
        variations = Variation.objects.filter(item=self).aggregate(avg=Avg('percent_discount'))
        if variations['avg'] is not None and self.count_program_valid():
            percent=int(variations['avg'])
        return percent

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
    class Meta:
        ordering=['value']
    def get_file(self):
        if self.image and hasattr(self.image,'url'):
            return self.image.url

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
    view=models.IntegerField(default=0)
    def __str__(self):
        return str(self.item)
    def get_absolute_url(self):
        return reverse("deal_shock", kwargs={"id": self.id})
    def update_percent(self):
        count_program=Shop_program.objects.filter(product=self.item,valid_to__gt=datetime.datetime.now()-datetime.timedelta(seconds=10)).count()
        if count_program==0:
            self.percent_discount=0

    def save(self, *args, **kwargs):
        self.update_percent()        
        super(Variation, self).save(*args, **kwargs)
        
    def discount_price_deal_shock(self):
        discount=0
        if self.percent_discount_deal_shock>0:
            discount= self.price*self.percent_discount_deal_shock/100
        return discount

    def total_discount(self):
        discount=0
        if self.percent_discount and self.item.count_program_valid() > 0:
            discount= self.price*(self.percent_discount)/100
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

class Byproductcart(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    byproduct=models.ForeignKey(Variation,on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity=models.IntegerField()
    def discount_deal_by(self):
        return self.quantity * self.byproduct.discount_price_deal_shock()
    def price_by(self):
        return self.quantity*self.byproduct.price
    def discount_by(self):
        total_discount=0
        if self.byproduct.item.count_program_valid()>0:
            total_discount=self.quantity*self.byproduct.price*(self.byproduct.percent_discount/100)
        return total_discount
    def total_price(self):
        return self.price_by()-self.discount_deal_by()-self.discount_by()
   
