from django.db import models
from django.contrib.auth.models import User
from django.db.models import Q
import uuid
from cloudinary_storage.storage import RawMediaCloudinaryStorage
from mimetypes import guess_type
import os
from shop.models import *
from checkout.models import *
# Create your models here.


class Thread(models.Model):
    participants=models.ManyToManyField(User,blank=True)
    group_name=models.CharField(max_length=200,null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
   
    def count_message_not_seen(self):
        return Message.objects.filter(seen=False,thread=self).count()
    def count_message(self):
        count=0
        return Message.objects.filter(thread=self).count()
    def message_last(self):
        if Message.objects.filter(message=self).exists():
            return Message.objects.filter(message=self).last()
    def info_thread(self):
        info=[]
        for user in self.participants.all():
            if Shop.objects.filter(user=user).exists():
                info.append({'shop_logo':Shop.objects.filter(user=user).first().logo.url,
                'shop_name':Shop.objects.filter(user=user).first().name,
                'user_id':user.id})
            else:
                info.append({'user_id':user.id,'username':user.username})
        return info
    
class UploadFile(models.Model):
    id = models.UUIDField(primary_key = True,default = uuid.uuid4,editable = False)
    upload_by=models.ForeignKey(User, on_delete=models.CASCADE)
    file=models.FileField(null=True,storage=RawMediaCloudinaryStorage())
    file_name=models.CharField(max_length=200,null=True)
    image_preview=models.FileField(null=True)
    duration=models.FloatField(null=True)
    upload_date=models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering=['-upload_date']
    def upload_file(self):
        if self.file and hasattr(self.file,'url'):
            return self.file.url
    def file_preview(self):
        if self.image_preview and hasattr(self.image_preview,'url'):
            return self.image_preview.url
    def filetype(self):
        type_tuple = guess_type(self.file.url, strict=True)
        if (type_tuple[0]).__contains__("image"):
            return "image"
        elif (type_tuple[0]).__contains__("video"):
            return "video"
        else:
            return 'pdf'
    def filename(self):
        return os.path.basename(self.file.name)
class Sticker(models.Model):
    image=models.ImageField()
    date_created = models.DateTimeField(auto_now=True)
    parent_id=models.IntegerField(blank=True,null=True)
class Message(models.Model):
    thread = models.ForeignKey(Thread, null=True, blank=True, on_delete=models.CASCADE, related_name='chatmessage_thread')
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True)
    message = models.TextField(null=True)
    product=models.ForeignKey(to='shop.Item', on_delete=models.CASCADE,null=True)
    order=models.ForeignKey(to='checkout.Order', on_delete=models.CASCADE,null=True)
    file=models.ManyToManyField(UploadFile,blank=True)
    seen = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now=True)
    def message_file(self):
        if UploadFile.objects.filter(message=self).exists():
            return UploadFile.objects.filter(message=self).first().file.url
    def message_filetype(self):
        if UploadFile.objects.filter(message=self).exists():
            return UploadFile.objects.filter(message=self).first().filetype()
    def message_product(self):
        list_item={}
        if Item.objects.filter(message=self).exists():
            item=Item.objects.filter(message=self).first()
            list_item['item_name']=item.name
            list_item['item_image']=item.media_upload.all()[0].upload_file()
            list_item['item_url']=item.get_absolute_url()
            list_item['item_max']=item.max_price()
            list_item['item_min']=item.min_price()
            list_item['percent_discount']=item.percent_discount()
            list_item['program_valid']=item.program_valid()
        return list_item
    def message_order(self):
        list_order={}
        if Order.objects.filter(message=self,ordered=True).exists():
            order=Order.objects.filter(message=self,ordered=True).first()
            list_order['id']=order.id
            list_order['received']=order.received
            list_order['canceled']=order.canceled
            list_order['total_quantity']=order.count_item_cart()
            list_order['being_delivered']=order.being_delivered
            list_order['order_url']=order.get_absolute_url()
            list_order['accepted']=order.accepted
            list_order['amount']=order.amount
            list_order['item_image']=order.items.all().last().product.item.media_upload.all()[0].upload_file()
            list_order['item_url']=order.items.all().last().product.item.get_absolute_url()
        return list_order


   

