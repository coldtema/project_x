from django.urls import path, include
from django.shortcuts import render
from apps.price_checker import views


urlpatterns = [
    path('', views.all_price_list, name='all_price_list_1'),
    path('update_prices/', views.update_prices, name='update_prices'),
    path('price_history/<int:id>', views.price_history, name='price_history'),
    path('delete_product/<int:id>', views.delete_product, name='delete_product'),
    path('price_history/delete_price/<int:id>', views.delete_price, name='delete_price')
]