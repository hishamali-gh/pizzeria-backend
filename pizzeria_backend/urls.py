from django.urls import path, include


urlpatterns = [
    path('auth/', include('accounts.urls')),
    path('user/', include('accounts.urls'))
]
