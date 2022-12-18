from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import *
@receiver(post_save, sender=User)
def create_user_shop(sender, instance, created, **kwargs):
	if created:
		Shop.objects.create(user=instance,name=instance.username)
@receiver(post_save, sender=User)
def save_user_shop(sender, instance, **kwargs):
	instance.shop.save()