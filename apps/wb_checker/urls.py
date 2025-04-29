from django.urls import path
from apps.wb_checker import views

app_name = 'wb_checker'



urlpatterns = [
    path('', views.WBCheckerMain.as_view(), name='all_price_list'),
    path('clear_db/', views.clear_db, name='clear_db'),
    path('update_prices/', views.update_prices, name='update_prices'),
    path('update_avaliability/', views.update_avaliability, name='update_avaliability'),
    path('update_all_menu_categories/', views.update_menu_categories, name='update_all_menu_categories'),
    path('update_top_prods/', views.update_top_prods, name='update_top_prods'),
    path('update_top_prods_info/', views.update_top_prods_info, name='update_top_prods_info'),
    path('recommendations/', views.RecommentationsList.as_view(), name='recommendations'),
]