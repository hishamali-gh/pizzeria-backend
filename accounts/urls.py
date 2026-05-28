from rest_framework_simplejwt.views import TokenRefreshView

from django.urls import path

from . import views


urlpatterns = [
    path('mfa/setup/', views.SetUpMFAAPIView.as_view(), name='mfa-setup'),
    path('mfa/verify-setup/', views.VerifyMFASetupAPIView.as_view(), name='mfa-verify-setup'),

    path('login/', views.LoginAPIView.as_view(), name='login'),
    path('mfa/verify-login/', views.VerifyMFALoginAPIView.as_view(), name='mfa-verify-login'),

    path('profile/', views.UserProfileAPIView.as_view(), name='profile'),

    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh')
]
