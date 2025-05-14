from django.urls import path, include
from django.shortcuts import render
from apps.price_checker import views


app_name = 'price_checker'

urlpatterns = [
    path('', views.PriceCheckerMain.as_view(), name='all_price_list'),
    path('disabled_prods/', views.DisabledProds.as_view(), name='disabled_prods'),
    path('update_prices/', views.update_prices, name='update_prices'),
    path('price_history/<int:id>', views.price_history, name='price_history'),
    path('delete_product/<int:id>', views.delete_product, name='delete_product'),
    path('price_history/delete_price/<int:id>', views.delete_price, name='delete_price'),
    path('share_product/<int:id>', views.ShareProduct.as_view(), name='share_product'),
    path('search_product/', views.SearchView.as_view(), name='search_product'),
    path('update_avaliability/', views.update_avaliability, name='update_avaliability')
]