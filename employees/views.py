from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from accounts.models import UserProfile

from .permissions import IsTenantAdmin
from .models import Employee, EmployeeInvitation
from .serializers import EmployeeInvitationSerializer


User = get_user_model()


class InviteStaffAPIView(APIView):
    permission_classes = [IsTenantAdmin]

    def get(self, request):
        token = request.query_params.get('token')
        invitation = get_object_or_404(EmployeeInvitation, token=token, is_used=False)

        if invitation.is_expired():
            return Response({"error": "Expired"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"email": invitation.email, "role": invitation.role})


    def post(self, request):
        serializer = EmployeeInvitationSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        
        invitation = serializer.save()

        subdomain = request.tenant.schema_name.replace('tenant_', '')
        
        invite_link = f"http://{subdomain}.localhost:5173/onboarding?token={invitation.token}"
        
        send_mail(
            subject="DCS Authorization Required",
            message=f"You have been authorized as {invitation.role}. Complete your setup here: {invite_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invitation.email],
            fail_silently=False,
        )
        
        return Response({"message": "Invitation dispatched.", 'token': invitation.token}, status=status.HTTP_201_CREATED)



class ClaimInviteAPIView(APIView):
    def post(self, request):
        token = request.data.get('token')
        password = request.data.get('password')

        tenant = request.tenant
        
        invitation = get_object_or_404(EmployeeInvitation, token=token, is_used=False)

        user = User.objects.create_user(
            email=invitation.email,
            password=password,
        )

        UserProfile.objects.create(
            user=user,
            full_name=invitation.email,
            tenant=tenant
        )

        Employee.objects.create(user=user, role=invitation.role)

        invitation.is_used = True
        invitation.save()
        
        return Response({'message': 'Handshake Complete'}, status=status.HTTP_201_CREATED)
