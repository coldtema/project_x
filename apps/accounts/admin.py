from django.contrib import admin
from .models import SubRequest, CustomUser

@admin.register(SubRequest)
class SubRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'price', 'duration', 'sub_plan', 'status', 'created']
    ordering = ['-created']
    


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display =  ['email', 'subscription', 'sub_expire', 'slots', 'dest_name', 'dest_id', 'discount_balance', 'notification_discount_price', 'notification_discount', 'pricedown_notification', 'priceup_notification']
    list_filter = ['subscription']
    ordering = ['-date_joined']