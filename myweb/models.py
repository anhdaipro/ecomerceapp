from django.db import models
from account.models import User
# Create your models here.
class Notify(models.Model):
    customer=models.ManyToManyField(User,blank=True)
    image=models.ImageField(null=True)
    message=models.CharField(max_length=1000)
class Image_home(models.Model):
    image=models.ImageField(null=True)
    url_field=models.URLField(max_length=200,null=True)