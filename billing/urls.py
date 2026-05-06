from django.urls import path
from .views import CreateRazorpayOrderAPIView, SubscriptionUpdateAPIView


urlpatterns = [
    path('order/create/', CreateRazorpayOrderAPIView.as_view(), name='create-order'),
    path('subscription/update/', SubscriptionUpdateAPIView.as_view(), name='update-subscription'),
]
