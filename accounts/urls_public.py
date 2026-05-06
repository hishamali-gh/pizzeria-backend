from django.urls import path
from accounts import views


urlpatterns = [
    path('register/', views.RegistrationAPIView.as_view(), name='register')
]
