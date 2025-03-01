import apps.blog.views as views
from django.urls import path, re_path, include


about_patterns = [
    path(r'<str:name>/<int:age>', views.about, name ='about_mod'),
    path(r'', views.about, name ='about_def'),
]

product_detailed_patterns = [
    path('', views.products_def, name='products_def_id'),
    path('questions/', views.products_def_questions, name='products_def_questions'),
    path('comments/', views.products_def_comments, name='products_def_comments'),
]

product_patterns = [
    path('new/', views.products_new, name='products_new'),
    path('top/', views.products_top, name='products_top'),
    path('', views.products_def, name='products_def'),
    path('<int:id>/', include(product_detailed_patterns))
]

urlpatterns = [
    path('', views.index, name='hello'), #путь, функция представления, и имя пути для лаконичности
    path(r'about/', include(about_patterns)),
    path('products/', include(product_patterns)),
    # path('message/<str:category>/<str:subcategory>/<str:theme>/<int:number>', views.message, name = 'message'),
    re_path(r'^message/(?P<category>[a-z]+?)/(?P<subcategory>\D+?)/(?P<theme>\D+?)/(?P<number>\d+)', views.message, name = 'message'),
    path('accounts/', views.accounts, name='accounts'),
    path('posts/', views.posts, name='posts'),
]