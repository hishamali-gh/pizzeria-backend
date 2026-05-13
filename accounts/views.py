import pyotp

import datetime

from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken

from django.contrib.auth import get_user_model

from accounts.serializers import RegistrationSerializer

from .serializers import LoginSerializer


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
                'user': user.profile.full_name,
                'tenant': user.profile.tenant.name if user.profile.tenant else 'System',
                'subdomain': user.profile.tenant.schema_name.replace('tenant_', '') if user.profile.tenant else 'admin', # Let's derive the subdomain name from the schema_name, at least for now, so we can reduce another database hit (we actually fetch the subdomain name from the 'domain' field of the Domain model).
                'plan': user.profile.tenant.currentsubscription.plan
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }
        }, status=status.HTTP_201_CREATED)


class SetUpMFAAPIView(APIView):
    permission_classes = [IsAuthenticated]


    def get(self, request):
        user = request.user

        if not user.mfa_secret:
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
        code = request.data.get('code').replace(' ', '')

        if not code:
            return Response({'error': 'Code required'}, status=status.HTTP_400_BAD_REQUEST)
        
        totp = pyotp.TOTP(user.mfa_secret)

        if totp.verify(code, valid_window=1):

            user.is_mfa_enabled = True

            user.save()

            return Response({'message': 'MFA enabled successfully'})
        
        return Response({'error': 'Invalid code'}, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []


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
                'user': user.profile.full_name,
                'tenant': user.profile.tenant.name if user.profile.tenant else 'System',
                'subdomain': user.profile.tenant.schema_name.replace('tenant_', '') if user.profile.tenant else 'admin',
                'plan': user.profile.tenant.currentsubscription.plan
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }
        })


class VerifyMFALoginAPIView(APIView):
    permission_classes = [AllowAny]


    def post(self, request):
        email = request.data.get('email')
        code = request.data.get('code')

        try:
            user = User.objects.get(email=email)
        
            totp = pyotp.totp.TOTP(user.mfa_secret)

            if totp.verify(code):
                refresh = RefreshToken.for_user(user)

                return Response({
                    'message': 'Successfully logged in!',
                    'data': {
                        'user': user.profile.full_name,
                        'tenant': user.profile.tenant.name if user.profile.tenant else 'System',
                        'subdomain': user.profile.tenant.schema_name.replace('tenant_', '') if user.profile.tenant else 'admin',
                        'plan': user.profile.tenant.currentsubscription.plan
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


class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]


    def get(self, request):
        user = request.user # Set by the JWTAuthentication class
        tenant = request.tenant # Set by the django-tenants middleware

        return Response({
            "identity": {
                "email": user.email,
                "full_name": user.profile.full_name
            },
            "other": {
                "role": user.employee_profile.role,
                "created_at": user.created_at,
                "is_mfa_enabled": user.is_mfa_enabled
            },
            "tenant": {
                "name": tenant.name
            }
        })


""" class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh')

        if refresh_token:
            request.data['refresh'] = refresh_token

        try:
            response = super().post(request, *args, **kwargs)
            
            if response.status_code == 200:
                new_access_token = response.data.get('access')
                
                response.set_cookie(
                    key='access',
                    value=new_access_token,
                    domain='.localhost',
                    httponly=False,
                    samesite='Lax'
                )
            return response

        except InvalidToken:
            return Response({"error": "Master session expired"}, status=status.HTTP_401_UNAUTHORIZED) """
