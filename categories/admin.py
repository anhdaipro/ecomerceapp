from django.contrib import admin

# Register your models here.
import admin_thumbnails

from mptt.admin import DraggableMPTTAdmin
from .models import *
from shop.models import *
from django.utils.html import format_html
class Image_categoryAdmin(admin.ModelAdmin):
    def image_tag(self, obj):
        return format_html('<img src="{}" style="background-position: 50%;background-size: contain;background-repeat: no-repeat;width: 200px;height: 100px;" />'.format(obj.image.url))
    image_tag.short_description = 'Image'

    list_display = ['id','image_tag',]


class CategoryAdmin2(DraggableMPTTAdmin):
    mptt_indent_field = "title"
    list_display = ('tree_actions', 'indented_title','id','tree_id','lft','rght',
                    'related_products_count', 'related_products_cumulative_count')
    list_display_links = ('indented_title',)
    prepopulated_fields = {'slug': ('title',)}
    actions = ['set_category']
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        # Add cumulative product count
        qs = Category.objects.add_related_count(
                qs,
                Item,
                'category',
                'products_cumulative_count',
                cumulative=True)

        # Add non cumulative product count
        qs = Category.objects.add_related_count(qs,
                    Item,
                    'category',
                    'products_count',
                    cumulative=False)
        return qs
    def set_category(self,request,queryset):
        for i in queryset:
            i.save()
    def related_products_count(self, instance):
        return instance.products_count
    related_products_count.short_description = 'Related products (for this specific category)'

    def related_products_cumulative_count(self, instance):
        return instance.products_cumulative_count
    related_products_cumulative_count.short_description = 'Related products (in tree)'   
admin.site.register(Category,CategoryAdmin2)
admin.site.register(Image_category,Image_categoryAdmin)
