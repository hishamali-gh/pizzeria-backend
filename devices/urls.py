from rest_framework.routers import DefaultRouter

from django.urls import path, include

from . import views 


router = DefaultRouter()

router.register(r'inventory', views.DeviceViewSet, basename='device')
router.register(r'alerts', views.AlertViewSet, basename='alert')


urlpatterns = [
    path('', include(router.urls)),
    path('ingest/', views.TelemetryIngestionAPIView.as_view(), name='telemetry-ingestion')
]
