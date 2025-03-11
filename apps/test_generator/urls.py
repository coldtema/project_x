from django.urls import path, include
from django.shortcuts import render
from apps.test_generator import views

urlpatterns = [
    path('', views.all_tests_list, name='test_generator'),
    path('pass_test/<int:id>', views.pass_test, name='pass_test'),
    path('delete_test/<int:id>', views.delete_test, name='delete_test'),
    path('pass_test/<int:id>/answers/', views.answers_on_test, name='answers_on_test'),
]