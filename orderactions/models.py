from django.db import models
from cloudinary_storage.storage import RawMediaCloudinaryStorage
# Create your models here.
from django.db import models
from carts.models import *
from orders.models import *
from django.contrib.auth.models import User
from shop.models import *
from mimetypes import guess_type
class Refund(models.Model):
    order = models.ForeignKey(to="orders.Order", on_delete=models.CASCADE)
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)
    image=models.ImageField(null=True)
    reason = models.TextField()
    accepted = models.BooleanField(default=False)
    email = models.EmailField()
    def __str__(self):
        return self.user.username
class CancelOrder(models.Model):
    order = models.ForeignKey(to="orders.Order", on_delete=models.CASCADE)
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    reason = models.CharField(max_length=200)

class ReView(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    cartitem = models.ForeignKey(to="carts.CartItem", on_delete=models.CASCADE,related_name='review_item')
    review_text = models.CharField(max_length=200,null=True)
    info_more=models.TextField(max_length=2000,null=True)
    review_rating = models.IntegerField(null=True)
    rating_product=models.IntegerField(null=True)
    xu=models.IntegerField(default=0)
    rating_seller_service=models.IntegerField(null=True)
    rating_shipping_service=models.IntegerField(null=True)
    created = models.DateTimeField(auto_now=True)
    anonymous_review=models.BooleanField(default=False)
    edited=models.BooleanField(default=False)
    like=models.ManyToManyField(User,blank=True,related_name='likers')
    class Meta:
        verbose_name_plural = 'Reviews'
    def __str__(self):
        return f"{self.pk}"
    def shop_name(self):
        name=''
        if self.user.shop:
            name=self.user.shop.name
        return name
    def num_like(self):
        return self.like.all().count()
    def get_reply(self):
        reply=Reply.objects.filter(review=self)
        if reply.exists():
            reply=reply.first()
            return({'text':reply.text,'created':reply.created})
    
class Media_review(models.Model):
    upload_by=models.ForeignKey(User,
                             on_delete=models.CASCADE)
    file=models.FileField(storage=RawMediaCloudinaryStorage())
    review=models.ForeignKey(ReView,on_delete=models.CASCADE,related_name='media_review')
    duration=models.IntegerField(null=True)
    media_preview=models.ImageField(null=True)


    def get_media_preview(self):
        if self.media_preview and hasattr(self.media_preview,'url'):
            return self.media_preview.url
    def filetype(self):
        type_tuple = guess_type(self.file.url, strict=True)
        if (type_tuple[0]).__contains__("image"):
            return "image"
        elif (type_tuple[0]).__contains__("video"):
            return "video"
class Report(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)
    review=models.ForeignKey(ReView,on_delete=models.CASCADE)
    reson=models.CharField(max_length=2000)
    created = models.DateTimeField(auto_now=True)
class Reply(models.Model):
    review=models.ForeignKey(ReView,on_delete=models.CASCADE)
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE)
    text=models.TextField(max_length=2000)
    created = models.DateTimeField(auto_now=True)