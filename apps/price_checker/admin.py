from django.contrib import admin
from .models import Product, Price, Shop, Tag

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'shop', 'latest_price', 'author', 'created', 'updated']
    list_filter = ['shop', 'author']
    search_fields = ['name']
    ordering = ['-created']

@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    list_display = ['price', 'added_time', 'product']
    list_filter = ['product__name']
    search_fields = ['product__name']
    ordering = ['added_time']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name']
    list_filter = ['name']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ['name', 'main_url', 'display_tags']
    list_filter = ['tags']
    search_fields = ['name', 'tags']
    ordering = ['name']

    def display_tags(self, obj):
        return ', '.join(tag.name for tag in obj.tags.all())