from django.urls import path
from apps.accounts import views


app_name = 'accounts'

urlpatterns = [
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('profile/', views.profile, name='profile'),
    path('profile_edit/', views.profile_edit, name='profile_edit'),
    path('subscription_edit/', views.subscription_edit, name='subscription_edit'),
    path('geolocation_edit/', views.GeolocationEditView.as_view(), name='geolocation_edit'),
    path('change_password/', views.change_password, name='change_password'),
    path('update_discount_balance/', views.update_discount_balance, name='update_discount_balance')
]