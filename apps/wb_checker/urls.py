from django.urls import path
from apps.wb_checker import views

app_name = 'wb_checker'



urlpatterns = [
    path('', views.WBCheckerMain.as_view(), name='all_price_list'),
    path('disabled_prods/', views.WBDisabledProds.as_view(), name='disabled_prods'),
    path('clear_db/', views.clear_db, name='clear_db'),
    path('update_prices/', views.update_prices, name='update_prices'),
    path('update_avaliability/', views.update_avaliability, name='update_avaliability'),
    path('update_all_menu_categories/', views.update_menu_categories, name='update_all_menu_categories'),
    path('update_top_prods/', views.update_top_prods, name='update_top_prods'),
    path('update_top_prods_info/', views.update_top_prods_info, name='update_top_prods_info'),
    path('recommendations/', views.RecommentationsList.as_view(), name='recommendations'),
    path('wb_product_details/<int:id>', views.wbproduct_details, name='wb_product_details'),
    path('delete_price/<int:id>', views.delete_price, name='delete_price'),
    path('delete_wb_product/<int:id>', views.delete_wb_product, name='delete_wb_product'),
    path('recommendations/recommendations_settings', views.RecommendationSettings.as_view(), name='recommendations_settings'),
    path('price_chart/<int:id>', views.price_chart, name='price_chart'),
]