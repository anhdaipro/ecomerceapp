from django.contrib import admin

# Register your models here.
from .models import *
class AddressAdmin(admin.ModelAdmin):
    list_display  = ['id','user','name','address_type']
admin.site.register(OrderItem,CartAdmin)