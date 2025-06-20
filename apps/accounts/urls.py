from django.urls import path
from apps.accounts import views


app_name = 'accounts'

urlpatterns = [
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('password_reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('profile/', views.profile, name='profile'),
    path('notification_edit/', views.notification_edit, name='notification_edit'),
    path('subscription_edit/', views.subscription_edit, name='subscription_edit'),
    path('geolocation_edit/', views.GeolocationEditView.as_view(), name='geolocation_edit'),
    path('subscription_edit/payment/', views.payment, name='payment'),
    path('subscription_edit/payment_history/', views.payment_history, name='payment_history')
]