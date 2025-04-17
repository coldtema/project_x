from django.urls import path
from apps.wb_checker import views

urlpatterns = [
    path('', views.all_price_list, name='all_price_list'),
    path('clear_db/', views.clear_db, name='clear_db'),
    path('update_prices/', views.update_prices, name='update_prices'),
    path('update_avaliability/', views.update_avaliability, name='update_avaliability'),
    path('update_all_menu_categories/', views.update_menu_categories, name='update_all_menu_categories'),
    path('load_test_data/', views.load_test_data, name='load_test_data')
]