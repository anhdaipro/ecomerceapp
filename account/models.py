from django.db import models
# Create your models here.
from django.contrib.auth.models import User
class Customer(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name='customer')
    name=models.CharField(max_length=100)
    image=models.ImageField(upload_to='profile/',null=True)
    USER_TYPE=(
        ('C','Customer'),
        ('S','Seller')
    )
    GENDER_CHOICE=(
        ('MALE','MALE'),
        ('FEMALE','FEMALE'),
        ('ORTHER','ORTHER')
    )
    user_type=models.CharField(max_length=10,choices=USER_TYPE,blank=True)
    gender=models.CharField(max_length=10,choices=GENDER_CHOICE,blank=True)
    phone_number=models.CharField(max_length=20)
    address=models.CharField(max_length=100)
    zip = models.CharField(max_length=100,blank=True)
    date_of_birth=models.DateField(null=True,blank=True)
    xu=models.IntegerField(null=True)
    is_online=models.DateTimeField(auto_now=True)
    online=models.BooleanField(default=False)
    def __str__(self):
        return self.user.username
    

class UserOTP(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    time_st=models.DateTimeField(auto_now=True)
    otp = models.SmallIntegerField()

