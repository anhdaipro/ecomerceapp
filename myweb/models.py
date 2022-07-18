from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class Notify(models.Model):
    customer=models.ManyToManyField(User,blank=True)
    image=models.ImageField(null=True)
    message=models.CharField(max_length=1000)
    read=models.BooleanField(default=False)


class Image_home(models.Model):
    upload_by=models.ForeignKey(User, on_delete=models.CASCADE,null=True)
    image=models.ImageField(null=True)
    url_field=models.URLField(max_length=200,null=True)
    def get_image(self):
        if self.image and hasattr(self.image,'url'):
            return self.image.url
class SearchKey(models.Model):
    keyword = models.CharField(max_length=255)
    total_searches = models.IntegerField(default=0)
    updated_on = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.keyword