from django.urls import path
from apps.core import views


app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('menu/', views.MenuView.as_view(), name='menu'),
    path('faq/', views.faq, name='faq'),
    path('contacts/', views.contacts, name='contacts')
]