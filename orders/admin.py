from django.contrib import admin

# Register your models here.
from django.utils import timezone
from .models import *
# Register your models here.
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id','user','ref_code','shop','ordered','being_delivered',
    'canceled','received','refund_requested','refund_granted','shipping_address'
    ,'ordered_date']
    list_display_links = ['user','shipping_address']
    list_filter = ['ordered','being_delivered','received','refund_requested','refund_granted']
    search_fields = ['user__username','ref_code']

    actions = ['set_order_received','set_order_being_delivered']

    def set_order_received(self,request,queryset):
        queryset.update(received=True,received_date=timezone.now())

    def set_order_being_delivered(self,request,queryset):
        queryset.update(being_delivered=True)

class PaymentAdmin(admin.ModelAdmin):
    list_display  = ['id','user','payment_number']
    
admin.site.register(Order,OrderAdmin)
admin.site.register(Payment,PaymentAdmin)