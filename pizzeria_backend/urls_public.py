from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),

    path('auth/', include('accounts.urls_public')),
    path('billing/', include('billing.urls'))

    # path('tenants/', include('tenants.urls')),
]
