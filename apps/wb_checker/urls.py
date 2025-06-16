from django.urls import path
from apps.wb_checker import views

app_name = 'wb_checker'



urlpatterns = [
    path('', views.WBCheckerMain.as_view(), name='all_price_list'),
    path('disabled_prods/', views.WBDisabledProds.as_view(), name='disabled_prods'),
    path('recommendations/', views.RecommentationsList.as_view(), name='recommendations'),
    path('wb_product_details/<int:id>', views.wbproduct_details, name='wb_product_details'),
    path('delete_price/<int:id>', views.delete_price, name='delete_price'),
    path('delete_wb_product/<int:id>', views.delete_wb_product, name='delete_wb_product'),
    path('recommendations/recommendations_settings', views.RecommendationSettings.as_view(), name='recommendations_settings'),
    path('price_chart/<int:id>', views.price_chart, name='price_chart'),
]