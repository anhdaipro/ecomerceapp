from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q
import uuid
from cloudinary_storage.storage import RawMediaCloudinaryStorage
from mimetypes import guess_type
import os
from shop.models import *
from orders.models import *
# Create your models here.
message_type_choice=(
    ('1','Message'),
    ('2','Image'),
    ('3','Video'),
    ('4',"Product"),
    ('5',"Order"),
    ('6','Other')
)
class Thread(models.Model):
    admin=models.ForeignKey(User, on_delete=models.CASCADE,null=True)
    participants=models.ManyToManyField(User,blank=True,related_name='participants')
    timestamp = models.DateTimeField(auto_now_add=True)
    def count_message_not_seen(self):
        return Message.objects.filter(seen=False,thread=self).count()
    def count_message(self):
        return Message.objects.filter(thread=self).count()
   
class Member(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='member_thread')
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='member_user')
    created = models.DateTimeField(auto_now=True)
    is_seen = models.BooleanField(default=True)
    count_message_unseen = models.IntegerField(default=0)
    block=models.BooleanField(default=False)
    ignore=models.BooleanField(default=False)
    gim=models.BooleanField(default=False)
class Sticker(models.Model):
    image=models.ImageField()
    date_created = models.DateTimeField(auto_now=True)
    parent_id=models.IntegerField(blank=True,null=True)

class Reportuser(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='report_thread')
    user=models.ForeignKey(User, on_delete=models.CASCADE,related_name='reporter')
    reported=models.ForeignKey(User, on_delete=models.CASCADE,related_name='reported_person')
    reason=models.CharField(max_length=100,default='Khác')
    description=models.TextField(blank=True)
    created = models.DateTimeField(auto_now=True)

class Mediareport(models.Model):
    image=models.ImageField()
    created = models.DateTimeField(auto_now=True)
    report=models.ForeignKey(Reportuser, on_delete=models.CASCADE)


class Message(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='chatmessage_thread')
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True)
    message = models.TextField(null=True)
    message_type=models.CharField(max_length=200,choices=message_type_choice,default='1')
    product=models.ForeignKey(to='shop.Item', on_delete=models.CASCADE,null=True,related_name='message_product')
    order=models.ForeignKey(to='orders.Order', on_delete=models.CASCADE,null=True,related_name='message_order')
    date_created = models.DateTimeField(auto_now=True)
    def message_product(self):
        if self.message_type=='4':
            return ({'name':self.product.name,'id':self.product_id,'slug':self.product.slug,
            'max_price':self.product.max_price(),'min_price':self.product.min_price(),
            'percent_discount':self.product.percent_discount(),
            'image':self.product.get_image_cover()})

    def message_order(self):
        if self.message_type=='5':
            return({'id':self.order.id,'received':self.order.received,'canceled':self.order.canceled,
            'accepted':self.order.accepted,'amount':self.order.amount,
            'image':self.order.items.all().last().get_image(),
            'url':self.order.items.all().last().item.slug,
            'total_quantity':self.order.count_item_cart(),
            'being_delivered':self.order.being_delivered})
           
class Messagemedia(models.Model):
    message= models.ForeignKey(Message, on_delete=models.CASCADE,related_name='message_media')
    upload_by=models.ForeignKey(User, on_delete=models.CASCADE)
    file=models.FileField(upload_to="chat/",storage=RawMediaCloudinaryStorage())
    file_preview=models.FileField(null=True,upload_to="chat/")
    duration=models.FloatField(default=0)
    upload_date=models.DateTimeField(auto_now_add=True)
    def get_file_preview(self):
        if self.file_preview and hasattr(self.file_preview,'url'):
            return self.file_preview.url
    def get_filetype(self):
        type_tuple = guess_type(self.file.url, strict=True)
        if (type_tuple[0]).__contains__("image"):
            return "image"
        else:
            return 'video'
    



   

