from django.urls import path
from apps.accounts import views


app_name = 'accounts'

urlpatterns = [
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('profile/', views.profile, name='profile'),
    path('notification_edit/', views.notification_edit, name='notification_edit'),
    path('subscription_edit/', views.subscription_edit, name='subscription_edit'),
    path('geolocation_edit/', views.GeolocationEditView.as_view(), name='geolocation_edit'),
    path('change_password/', views.change_password, name='change_password'),
]