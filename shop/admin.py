from django.contrib import admin
from .models import *
import re
# Register your models here.
admin.site.register(Shop)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['id','name','shop']
    actions = ['set_category']
    def set_category(self,request,queryset):
        for i in queryset:
            i.slug=re.sub('[,./\ & ]', "-",i.name) + '.' + str(i.id)
            i.save()
class VariationAdmin(admin.ModelAdmin):
    list_display = ['id','color','size','price','inventory']
class CommentAdmin(admin.ModelAdmin):
    list_display=['user','comment','parent']
class ShopviewAdmin(admin.ModelAdmin):
    list_display=['user','shop','create_at']
class ItemviewAdmin(admin.ModelAdmin):
    list_display=['user','item','create_at']
admin.site.register(ShopViews,ShopviewAdmin)
admin.site.register(ItemViews,ItemviewAdmin)
admin.site.register(Item,ItemAdmin)
admin.site.register(Variation,VariationAdmin)
admin.site.register(Color)
admin.site.register(Size)
admin.site.register(UploadItem)

