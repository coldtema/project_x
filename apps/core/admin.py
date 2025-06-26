from django.contrib import admin
from .models import Post, Notification

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'text', 'date']



@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'time', 'additional_link']
    list_filter = ['user']
    ordering = ['-time']
