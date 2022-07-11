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
    ('5',"Order")
)
class Thread(models.Model):
    participants=models.ManyToManyField(User,blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    def count_message_not_seen(self):
        return Message.objects.filter(seen=False,thread=self).count()
    def count_message(self):
        count=0
        return Message.objects.filter(thread=self).count()
   
class Member(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='member_thread')
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='member_user')
    created = models.DateTimeField(auto_now=True)
    is_seen = models.BooleanField(default=False)
    block=models.BooleanField(default=False)
    ignore=models.BooleanField(default=False)
    gim=models.BooleanField(default=False)
class Sticker(models.Model):
    image=models.ImageField()
    date_created = models.DateTimeField(auto_now=True)
    parent_id=models.IntegerField(blank=True,null=True)
class Message(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='chatmessage_thread')
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True)
    message = models.TextField(null=True)
    message_type=models.CharField(max_length=200,choices=message_type_choice,default='1')
    product=models.ForeignKey(to='shop.Item', on_delete=models.CASCADE,null=True,related_name='message_product')
    order=models.ForeignKey(to='orders.Order', on_delete=models.CASCADE,null=True,related_name='message_order')
    date_created = models.DateTimeField(auto_now=True)
    
    def message_product(self):
        if self.product:
            return ({'name':self.product.name,'id':self.product_id,'slug':self.product.get_absolute_url(),
            'max_price':self.product.max_price(),'min_price':self.product.min_price(),
            'percent_discount':self.product.percent_discount(),
            'program_valid':self.product.program_valid(),'image':self.product.get_media_cover()})

    def message_order(self):
        if self.order:
            return({'id':self.order.id,'received':self.order.received,'canceled':self.order.canceled,
            'accepted':self.order.accepted,'amount':self.order.amount,
            'item_image':self.order.items.all().last().get_image(),
            'item_url':self.order.items.all().last().item.get_absolute_url(),
            'total_quantity':self.order.total_quantity,
            'being_delivered':self.order.being_delivered})
           
class Messagemedia(models.Model):
    message= models.ForeignKey(Message, on_delete=models.CASCADE,related_name='message_media')
    upload_by=models.ForeignKey(User, on_delete=models.CASCADE)
    file=models.FileField(upload_to="chat/")
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
    



   

