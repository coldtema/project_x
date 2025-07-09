from django.urls import path
from apps.core import views
import os


app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('menu/', views.MenuView.as_view(), name='menu'),
    path('faq/', views.faq, name='faq'),
    path('contacts/', views.contacts, name='contacts'),
    path('delete_notification/<int:id>', views.delete_notification, name='delete_notification'),
    path('notifications_swap/', views.notifications_swap, name='notifications_swap'),
    path('guide/', views.guide, name='guide'),
    path(f'bot/{os.getenv("WEBHOOK_TOKEN")}/webhook/', views.bot_webhook, name='bot_webhook'),
]