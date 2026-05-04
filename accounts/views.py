from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

import pyotp

from django_tenants.utils import schema_context

from django.contrib.auth import get_user_model

from accounts.serializers import RegistrationSerializer
from .serializers import LoginSerializer
from .models import UserTenantMapper


User = get_user_model()


class RegistrationAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        return Response({
            'message': 'Registration completed!',
            'data': {
                'user': user.full_name,
                'tenant': user.tenant.name,
                'subdomain': user.tenant.schema_name.replace('tenant_', ''), # Let's derive the subdomain name from the schema_name, at least for now, so we can reduce another database hit (we actually fetch the subdomain name from the 'domain' field of the Domain model).
                'plan': user.tenant.currentsubscription.plan
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }
        }, status=status.HTTP_201_CREATED)


class SetUpMFAAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if not user.is_mfa_enabled:
            user.generate_mfa_secret()

        otp_uri = user.get_totp_uri()

        return Response({
            'otp_uri': otp_uri,
            'mfa_enabled': user.is_mfa_enabled
        })
    

class VerifyMFASetupAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        code = request.data.get('code')

        if not code:
            return Response({'error': 'Code required'}, status=status.HTTP_400_BAD_REQUEST)
        
        totp = pyotp.TOTP(user.mfa_secret)

        if totp.verify(code):
            user.is_mfa_enabled = True

            user.save()

            return Response({'message': 'MFA enabled successfully'})
        
        return Response({'error': 'Invalid code'}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})

        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data.get('user')


        # MFA FLOW

        if user.is_mfa_enabled:
            return Response({
                'message': 'Secondary authentication required',
                'mfa_required': True,
                'email': user.email
            }, status=status.HTTP_202_ACCEPTED)

        
        # NORMAL FLOW

        refresh = RefreshToken.for_user(user)

        return Response({
            'message': 'Successfully logged in!',
            'data': {
                'user': user.full_name,
                'tenant': user.tenant.name,
                'subdomain': user.tenant.schema_name.replace('tenant_', ''),
                'plan': user.tenant.currentsubscription.plan
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }
        })


class VerifyMFALoginAPIView(APIView):
    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')

        try:
            mapping = UserTenantMapper.objects.get(email=email)
            target_tenant = mapping.tenant
        
        except UserTenantMapper.DoesNotExist:
            return Response({'error': 'Identity not found'}, status=status.HTTP_400_BAD_REQUEST)

        with schema_context(target_tenant.schema_name):
            try:
                user = User.objects.get(email=email)

                if not user.is_mfa_enabled:
                    return Response({'error': 'MFA not enabled'}, status=status.HTTP_400_BAD_REQUEST)

                totp = pyotp.totp.TOTP(user.mfa_secret)

                if totp.verify(code):
                    refresh = RefreshToken.for_user(user)

                    return Response({
                        'message': 'Successfully logged in!',
                        'data': {
                            'user': user.full_name,
                            'tenant': user.tenant.name,
                            'subdomain': user.tenant.schema_name.replace('tenant_', ''),
                            'plan': user.tenant.currentsubscription.plan
                        },
                        'tokens': {
                            'refresh': str(refresh),
                            'access': str(refresh.access_token)
                        }
                    })
                else:
                    return Response({'error': 'Invalid security code'}, status=status.HTTP_401_UNAUTHORIZED)
            
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_400_BAD_REQUEST)
