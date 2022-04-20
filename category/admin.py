from django.contrib import admin

# Register your models here.
import admin_thumbnails

from mptt.admin import DraggableMPTTAdmin
from .models import *
from shop.models import *
class CategoryAdmin2(DraggableMPTTAdmin):
    mptt_indent_field = "title"
    list_display = ('tree_actions', 'indented_title','id',
                    'related_products_count', 'related_products_cumulative_count')
    list_display_links = ('indented_title',)
    prepopulated_fields = {'slug': ('title',)}
    actions = ['set_category','set_choice']
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
            i.slug=re.sub('---', "-",i.name) + '.' + str(i.id)
            i.save()
    def set_choice(self,request,queryset):
        queryset.update(choice=True)
    def related_products_count(self, instance):
        return instance.products_count
    related_products_count.short_description = 'Related products (for this specific category)'

    def related_products_cumulative_count(self, instance):
        return instance.products_cumulative_count
    related_products_cumulative_count.short_description = 'Related products (in tree)'   
admin.site.register(Category,CategoryAdmin2)
admin.site.register(Image_category)
