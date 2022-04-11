from django.db import models

# Create your models here.
from django.utils import timezone
from django.contrib.auth.models import User
ACTIVE_CHOICE=(
    ('Yes','Yes'),
    ('No','No')
)
# Create your models here.
class Shipping(models.Model):
    method=models.CharField(max_length=100)
    shipping_unit = models.CharField(max_length=100,null=True)
    tax_code=models.CharField(max_length=100,null=True)
    allowable_volume= models.IntegerField(null=True)
    def __str__(self):
        return str(self.method)
