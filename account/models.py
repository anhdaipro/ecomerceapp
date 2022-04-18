from django.db import models
from django.contrib.auth.models import User
import logging
# Create your models here.
from randompinfield import RandomPinField
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from django.conf import settings
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
    phone_number = PhoneNumberField(default='1234567')
    image=models.ImageField(upload_to='shop/',default='v1649469077/file/shop/3fb459e3449905545701b418e8220334_tn_jbplnr.png')
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
                return False
            else:
                return True
        else:
            return False

class UserOTP(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    time_st=models.DateTimeField(auto_now=True)
    otp = models.SmallIntegerField()
class OTP(models.Model):
    name = models.CharField(max_length=100)
    score = models.IntegerField(default=0)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.score >= 70:
            account_sid = settings.TWILIO_ACCOUNT_SID
            auth_token = settings.TWILIO_AUTH_TOKEN
            client = Client(account_sid, auth_token)

            message = client.messages.create(
                body=f"Congratulations {self.name}, your score is {self.score}",
                from_=settings.TWILIO_FROM_NUMBER,
                to='+84347285910'
            )
        else:
            account_sid = settings.TWILIO_ACCOUNT_SID,
            auth_token = settings.TWILIO_AUTH_TOKEN,
            client = Client(account_sid, auth_token)

            message = client.messages.create(
                body=f"Sorry {self.name}, your score is {self.score}. Try again",
                from_=settings.TWILIO_FROM_NUMBER,
                to='+84347285910'
            )

        print(message.sid)
        return super().save(*args, **kwargs)
class SMSVerification(models.Model):
    verified = models.BooleanField(default=False)
    pin = RandomPinField(length=6)
    sent = models.BooleanField(default=False)
    profile = models.ForeignKey(Profile, on_delete = models.CASCADE,null=True)

    def save(self, *args, **kwargs):
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=f"Ma xac minh la {self.pin}",
            from_=settings.TWILIO_FROM_NUMBER,
            to=str(self.profile.phone_number)
        )
        print(message.sid)
        return super().save(*args, **kwargs)

