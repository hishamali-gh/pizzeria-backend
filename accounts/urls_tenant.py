from django.urls import path
from . import views


urlpatterns = [
    path('mfa/setup/', views.SetUpMFAAPIView.as_view(), name='mfa-setup'),
    path('mfa/verify-setup/', views.VerifyMFASetupAPIView.as_view(), name='mfa-verify-setup'),
]
