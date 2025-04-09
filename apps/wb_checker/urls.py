from django.urls import path
from apps.wb_checker import views

urlpatterns = [
    path('', views.all_price_list, name='all_price_list'),
    path('clear_db/', views.clear_db, name='clear_db'),
    path('update_categories/', views.update_brands_categories, name='update_categories'),
    path('update_prices/', views.update_prices, name='update_prices'),
    path('update_avaliability/', views.update_avaliability, name='update_avaliability'),
    path('load_test_data', views.load_test_data, name='load_test_data')
]