from django.urls import path, include
from django.shortcuts import render
from apps.price_checker import views


urlpatterns = [
    path('', views.all_price_list, name='all_price_list'),
    
]