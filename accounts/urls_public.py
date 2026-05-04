from django.urls import path
from accounts import views


urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    path('mfa/verify-login/', views.VerifyMFALoginAPIView.as_view(), name='mfa-verify-login'),

    path('register/', views.RegistrationAPIView.as_view(), name='register')
]
