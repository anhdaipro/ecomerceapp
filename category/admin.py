from django.contrib import admin

# Register your models here.
import admin_thumbnails

from mptt.admin import DraggableMPTTAdmin
from .models import *
from shop.models import *


admin.site.register(Category)
admin.site.register(Image_category)
