from django.contrib import admin
from .models import WBBrand, WBSeller, WBMenuCategory, WBProduct, WBDetailedInfo
from django.db import models

@admin.register(WBBrand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'wb_id', 'main_url', 'subs_count']
    search_fields = ['name', 'wb_id']

    def get_queryset(self, request):
        old_qs = super().get_queryset(request)
        return old_qs.annotate(subs_count=models.Count('subs')).order_by('-subs_count')

    def subs_count(self, obj):
        return obj.subs_count


@admin.register(WBSeller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ['name', 'wb_id', 'main_url', 'subs_count']
    search_fields = ['name', 'wb_id']

    def get_queryset(self, request):
        old_qs = super().get_queryset(request)
        return old_qs.annotate(subs_count=models.Count('subs')).order_by('-subs_count')

    def subs_count(self, obj):
        return obj.subs_count


@admin.register(WBMenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'wb_id', 'main_url', 'subs_count']
    search_fields = ['name', 'wb_id']

    def get_queryset(self, request):
        old_qs = super().get_queryset(request)
        return old_qs.annotate(subs_count=models.Count('subs')).order_by('-subs_count')

    def subs_count(self, obj):
        return obj.subs_count



@admin.register(WBProduct)
class WBProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'artikul', 'brand', 'seller']
    search_fields = ['name', 'artikul', 'brand__name', 'seller__name']
    ordering = ['name']


@admin.register(WBDetailedInfo)
class WBDetailedInfoAdmin(admin.ModelAdmin):
    list_display = ['product', 'latest_price', 'author', 'created', 'enabled', 'size', 'volume']
    list_filter = ['author', 'enabled']
    search_fields = ['product__name']
    ordering = ['-created']