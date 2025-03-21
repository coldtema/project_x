from django.contrib import admin
from .models import Product, Price, Shop, Tag

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'shop', 'latest_price', 'created', 'updated', 'author']
    list_filter = ['shop', 'author__nickname']
    search_fields = ['name']
    ordering = ['-updated']

@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    list_display = ['price', 'added_time', 'product']
    list_filter = ['product__name']
    search_fields = ['product__name']
    ordering = ['price']


@admin.register(Tag)
class PriceAdmin(admin.ModelAdmin):
    list_display = ['name']
    list_filter = ['name']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Shop)
class PriceAdmin(admin.ModelAdmin):
    list_display = ['name']
    list_filter = ['tags']
    search_fields = ['name', 'tags']
    ordering = ['name']