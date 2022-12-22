from django.db import models

# Create your models here.
from django.conf import settings
from django.db import models
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel 
from django.db.models import Q
from django.urls import reverse
from slugify import slugify
import re

class Image_category(models.Model):
    image=models.ImageField(upload_to='category/')
    url_field=models.URLField(max_length=200)
class Category(models.Model):
    parent = models.ForeignKey('self',blank=True, null=True ,related_name='children', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    image=models.ImageField(blank=True,upload_to='category/')
    display=models.BooleanField(default=False)
    level=models.IntegerField(default=1)
    image_category=models.ManyToManyField(Image_category,blank=True)
    slug = models.SlugField(max_length=100,null=True,blank=True)
    choice=models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        #this line below give to the instance slug field a slug name
        self.slug = slugify(self.title)
        #this line below save every fields of the model instance
        super(Category, self).save(*args, **kwargs) 
    
        # At this point obj.val is still 1, but the value in the database
        # was updated to 2. The object's updated value needs to be reloaded
        # from the database.
   
    class Meta:
        verbose_name_plural = 'Categories'
        ordering=['id']
    # to undrestand better the parrent and child i'm gonna separated by '/' from each other
   
    def get_image(self):
        if self.image and hasattr(self.image,'url'):
            return self.image.url
   
    

'''class UrlHit(models.Model):
    url     = models.URLField()
    hits    = models.PositiveIntegerField(default=0)

    def __str__(self):
        return str(self.url)

    def increase(self):
        self.hits += 1
        self.save()


class HitCount(models.Model):
    url_hit = models.ForeignKey(UrlHit, editable=False, on_delete=models.CASCADE)
    ip      = models.CharField(max_length=40)
    session = models.CharField(max_length=40)
    date    = models.DateTimeField(auto_now=True)'''