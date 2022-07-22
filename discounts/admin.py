from django.contrib import admin

# Register your models here.
from .models import *
admin.site.register(Voucher)
admin.site.register(Buy_with_shock_deal)
admin.site.register(Promotion_combo)
admin.site.register(Shop_program)
admin.site.register(Flash_sale)