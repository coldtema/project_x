from django.urls import path
from apps.wb_checker import views

urlpatterns = [
    path('', views.all_price_list, name='all_price_list'),
    path('clear_db/', views.clear_db, name='clear_db')
]