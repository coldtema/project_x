from django.contrib import admin
from .models import WBBrand, WBSeller, WBMenuCategory, WBProduct

@admin.register(WBBrand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name']
    list_filter = ['name']
    search_fields = ['name']
    ordering = ['name']


@admin.register(WBSeller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ['name']
    list_filter = ['name']
    search_fields = ['name']
    ordering = ['name'] 




@admin.register(WBMenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    list_filter = ['name']
    search_fields = ['name']
    ordering = ['name'] 



@admin.register(WBProduct)
class WBProductAdmin(admin.ModelAdmin):
    list_display = ['name']
    list_filter = ['name']
    search_fields = ['name']
    ordering = ['name'] 