from django.db import models
from django.contrib.auth.models import User
import logging
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
    auth_token = models.CharField(max_length=100 )
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    phone = PhoneNumberField(null=True)
    image=models.ImageField(upload_to="profile/",default='no_user_mn2igp')
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
    date_of_birth=models.DateField(null=True,blank=True)
    xu=models.IntegerField(default=0,null=True)
    is_online=models.DateTimeField(auto_now=True)
    online=models.BooleanField(default=False)
    def __str__(self):
        return "%s" % self.user.username

    @property
    def last_seen(self):
        return cache.get(f"seen_{self.user.username}")

    @property
    def online(self):
        if self.last_seen:
            now = datetime.now(timezone.utc)
            if now > self.last_seen + timedelta(minutes=settings.USER_ONLINE_TIMEOUT):
                self.online=True
                self.save()
                return False

            else:
                return True
        else:
            self.online=True
            self.save()
            return False

class SMSVerification(models.Model):
    verified = models.BooleanField(default=False)
    pin = RandomPinField(length=6)
    phone = models.CharField(max_length=100,null=True)
    created = models.DateTimeField(auto_now_add=True)

