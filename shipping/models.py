from django.db import models

# Create your models here.
from django.utils import timezone
from django.contrib.auth.models import User
ACTIVE_CHOICE=(
    ('Yes','Yes'),
    ('No','No')
)
# Create your models here.
class Shipping_unit(models.Model):
    name=models.CharField(max_length=1000)
    tax_code=models.CharField(max_length=1000)
class Shipping(models.Model):
    method=models.CharField(max_length=100)
    shipping_unit = models.ManyToManyField(Shipping_unit)
    allowable_volume= models.IntegerField(null=True)
    def __str__(self):
        return str(self.method)
