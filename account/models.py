from django.db import models
from django.contrib.auth.models import User
import logging
import datetime

# Create your models here.
from randompinfield import RandomPinField
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
class Profile(models.Model):
    user = models.OneToOneField(User , on_delete=models.CASCADE,null=True)
    name=models.CharField(max_length=100,null=True )
    bio=models.TextField(null=True)
    is_verified = models.BooleanField(default=False)
    username_edit=models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    phone = PhoneNumberField(null=True)
    count_notifi_unseen=models.IntegerField(default=0,null=True)
    avatar=models.ImageField(upload_to="profile/",default='no_user_ypl5wh.png')
    USER_TYPE=(
        ('C','Customer'),
        ('S','Seller')
    )
    GENDER_CHOICE=(
        ('MALE','MALE'),
        ('FEMALE','FEMALE'),
        ('ORTHER','ORTHER')
    )
    user_type=models.CharField(max_length=10,choices=USER_TYPE,blank=True,default='C')
    gender=models.CharField(max_length=10,choices=GENDER_CHOICE,blank=True)
    date_of_birth=models.DateField(null=True)
    xu=models.IntegerField(default=0,null=True)
    is_online=models.DateTimeField(auto_now=True)
    online=models.BooleanField(default=False)
    def __str__(self):
        return "%s" % self.user.username

class SMSVerification(models.Model):
    verified = models.BooleanField(default=False)
    pin = RandomPinField(length=6)
    phone = models.CharField(max_length=100,null=True)
    created = models.DateTimeField(auto_now_add=True)

class Verifylink(models.Model):
    code=models.CharField(max_length=10)
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

class Verifyemail(models.Model):
    otp=RandomPinField(length=6,null=True)
    email=models.CharField(max_length=50,null=True)
    created = models.DateTimeField(auto_now_add=True)
ADDRESS_CHOICES = (
    ('B', 'Billing'),
    ('S', 'Shipping'),
)
class Address(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    name=models.CharField(max_length=100)
    address=models.CharField(max_length=100)
    city=models.CharField(max_length=100)
    district=models.CharField(max_length=100)
    town=models.CharField(max_length=100)
    phone_number=models.CharField(max_length=20)
    address_choice=models.CharField(max_length=20)
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    zip = models.CharField(max_length=100,null=True)
    default = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username
    class Meta:
        verbose_name_plural = 'Addresses'