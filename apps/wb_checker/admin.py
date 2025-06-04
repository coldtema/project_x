from django.contrib import admin
from .models import WBBrand, WBSeller, WBMenuCategory, WBProduct

@admin.register(WBBrand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name']
    list_filter = ['name']
    search_fields = ['name']
    ordering = ['name'] 