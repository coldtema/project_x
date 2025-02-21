import apps.blog.views as views
from django.urls import path, re_path

urlpatterns = [
    path('', views.index, name='hello'), #путь, функция представления, и имя пути для лаконичности
    path(r'about/<str:name>/<int:age>', views.about, name ='about_mod'),
    path(r'about/', views.about, name ='about_def'),
    path('contacts', views.contacts, name='contacts')
]