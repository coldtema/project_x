from django.urls import path, include
from django.shortcuts import render
from apps.test_generator import views

urlpatterns = [
    path('', views.all_tests_list, name='test_generator'),
]