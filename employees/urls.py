from django.urls import path

from . import views


urlpatterns = [
    path('invite-staff/', views.InviteStaffAPIView.as_view(), name='invite-staff'),
    path('claim-invite/', views.ClaimInviteAPIView.as_view(), name='claim-invite')
]
