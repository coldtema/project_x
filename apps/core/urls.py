from django.urls import path
from apps.core import views


app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('menu/', views.MenuView.as_view(), name='menu'),
    path('faq/', views.faq, name='faq'),
    path('contacts/', views.contacts, name='contacts'),
    path('delete_notification/<int:id>', views.delete_notification, name='delete_notification'),
    path('notifications_swap/', views.notifications_swap, name='notifications_swap')
]