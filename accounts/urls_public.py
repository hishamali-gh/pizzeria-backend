from rest_framework_simplejwt.views import TokenRefreshView

from django.urls import path

from . import views


urlpatterns = [
    path('register/', views.RegistrationAPIView.as_view(), name='register'),
    path('login/', views.LoginAPIView.as_view(), name='login'),

    path('profile/', views.UserProfileAPIView.as_view(), name='profile'),

    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh')
]
