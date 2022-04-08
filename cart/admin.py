from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.utils import timezone
from .models import *
class CartAdmin(admin.ModelAdmin):
    list_display  = ['id','user','product','quantity',]
admin.site.register(OrderItem,CartAdmin)