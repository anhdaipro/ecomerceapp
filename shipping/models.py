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
    shipping_unit = models.CharField(max_length=1000)
    allowable_volume= models.IntegerField(null=True)
    def __str__(self):
        return str(self.method)