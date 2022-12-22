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


class Category(MPTTModel):
    parent = TreeForeignKey('self',blank=True, null=True ,related_name='children', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    image=models.ImageField(blank=True)
    display=models.BooleanField(default=False)
    image_category=models.ManyToManyField(Image_category,blank=True)
    slug = models.SlugField(max_length=100,null=True,blank=True)
    choice=models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering=['id']
    
    # to undrestand better the parrent and child i'm gonna separated by '/' from each other
    def __str__(self):
        full_path = [self.title]
        c = self.parent
        while c is not None:
            full_path.append(c.title)
            c = c.parent
        return '/'.join(full_path[::-1])

    def get_full_id(self):
        list_id=[self.id]
        c=self.parent
        while c is not None:
            list_id.append(c.id)
            c=c.parent
        return list_id

    def get_full_category(self):
        full_path = [self.title]
        c = self.parent
        while c is not None:
            full_path.append(c.title)
            c = c.parent
        return '>'.join(full_path[::-1])
    def getparent(self):
        if self.parent!=None:
            return self.parent.id
    def save(self, *args, **kwargs):
        #this line below give to the instance slug field a slug name
        self.slug = slugify(self.title)
        #this line below save every fields of the model instance
        super(Category, self).save(*args, **kwargs) 
    
    class MPTTMeta:
        order_insertion_by=['id']
    def get_model_fields(model):
        fields = {}
        options = model._meta
        for field in sorted(options.concrete_fields + options.many_to_many):
            fields[field.name] = field
        return fields
   
    
        
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