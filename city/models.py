from django.db import models

# Create your models here.
class City(models.Model):
    maqh=models.CharField(max_length=100,null=True)
    matp=models.CharField(max_length=100,null=True)
    name=models.CharField(max_length=100)
    level=models.IntegerField()
