from django.urls import path
from . import views


urlpatterns = [
    path('login/', views.LoginView.as_view(), name='login'),
    # path('mfa/verify-login/', views.VerifyMFALoginAPIView.as_view(), name='mfa-verify-login'),

    path('mfa/setup/', views.SetUpMFAAPIView.as_view(), name='mfa-setup'),
    path('mfa/verify-setup/', views.VerifyMFASetupAPIView.as_view(), name='mfa-verify-setup'),
]
