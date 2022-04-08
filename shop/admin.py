from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Shop)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['id','name','shop']


class VariationAdmin(admin.ModelAdmin):
    list_display = ['id','color','size','price','percent_discount','percent_discount_deal_shock','inventory','percent_discount_flash_sale']
class CommentAdmin(admin.ModelAdmin):
    list_display=['user','comment','parent']



admin.site.register(Item,ItemAdmin)
admin.site.register(Variation,VariationAdmin)
admin.site.register(Color)
admin.site.register(Size)
admin.site.register(Buy_more_discount)
admin.site.register(Byproductcart)
admin.site.register(UploadItem)

