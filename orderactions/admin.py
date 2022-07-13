from django.contrib import admin

# Register your models here.
from .models import *
admin.site.register(ReView)
admin.site.register(Media_review)
admin.site.register(CancelOrder)