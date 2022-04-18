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
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
class Profile(models.Model):
    user = models.OneToOneField(User , on_delete=models.CASCADE,null=True)
    auth_token = models.CharField(max_length=100 )
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    phone_number = models.CharField(max_length=50,null=True)
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

class SMSVerification(models.Model):
    verified = models.BooleanField(default=False)
    pin = RandomPinField(length=6)
    sent = models.BooleanField(default=False)
    profile = models.ForeignKey(Profile, on_delete = models.CASCADE,null=True)

    def send_confirmation(self):

        logging.debug("Sending PIN %s to phone %s" % (self.pin, self.phone))

        if all(
            [
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN,
                settings.TWILIO_FROM_NUMBER,
            ]
        ):
            try:
                twilio_client = Client(
                    settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN
                )
                twilio_client.messages.create(
                    body="Your forgeter activation code is %s" % self.pin,
                    to=str(self.profile.phone_number),
                    from_=settings.TWILIO_FROM_NUMBER,
                )
                self.sent = True
                self.save()
                return True
            except TwilioRestException as e:
                logging.error(e)
        else:
            logging.warning("Twilio credentials are not set")

    def confirm(self, pin):
        if pin == self.pin and self.verified == False:
            self.verified = True
            self.save()
        else:
            raise NotAcceptable("your Pin is wrong, or this phone is verified before.")

        return self.verified

@receiver(post_save, sender=Profile)
def send_sms_verification(sender, instance, *args, **kwargs):
    try:
        sms = instance.user.sms
        if sms:
            pin = sms.pin
            sms.delete()
            verification = SMSVerification.objects.create(
                user=instance.user,
                phone=instance.user.profile.phone_number,
                sent=True,
                verified=True,
                pin=pin,
            )
    except:
        if instance.user.profile.phone_number:
            verification = SMSVerification.objects.create(
                user=instance.user, phone=instance.user.profile.phone_number
            )
            # TODO Remove send confirm from here and make view for it.
            

