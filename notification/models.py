from django.db import models

# Create your models here.
from django.shortcuts import render

# Create your views here.
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
class Notification(models.Model):
    MARKED_READ = "r"
    MARKED_UNREAD = "u"
    CHOICES = ((MARKED_READ, "read"), (MARKED_UNREAD, "unread"))
    user = models.ForeignKey(
        User, related_name="notifications", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=250, blank=True, null=True)
    body = models.TextField(blank=True, null=True)
    status = models.CharField(choices=CHOICES, default=MARKED_UNREAD, max_length=1)