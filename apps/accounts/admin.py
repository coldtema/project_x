from django.contrib import admin
from .models import SubRequest, CustomUser

@admin.register(SubRequest)
class SubRequestAdmin(admin.ModelAdmin):
    list_display = ['price', 'duration', 'sub_plan', 'user', 'status', 'created']
    ordering = ['-created']
    


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display =  ['email', 'subscription', 'sub_expire', 'slots', 'dest_name', 'dest_id', 'discount_balance', 'notification_discount_price', 'notification_discount', 'pricedown_notification', 'priceup_notification']
    ordering = ['-date_joined']