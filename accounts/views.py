import pyotp

""" import datetime """

from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

""" from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken """

from django_tenants.utils import schema_context

from django.contrib.auth import get_user_model
from django.db import connection

from employees.models import Employee
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

        tenant = user.profile.tenant
        subscription = getattr(tenant, 'currentsubscription', None)

        refresh = RefreshToken.for_user(user)


        return Response({
            'message': 'Registration successful!',
            'data': {
                'user': user.profile.full_name,
                'tenant': tenant.name if tenant else 'System',
                'role': 'admin', # Since admin is the one who registers the tenant.
                'subdomain': tenant.schema_name.replace('tenant_', '') if tenant else None,
                'plan': subscription.plan if subscription else None
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

        if not user.mfa_secret:
            return Response({'error': 'MFA setup not initialized'}, status=status.HTTP_400_BAD_REQUEST)

        raw_code = request.data.get('code')

        if not raw_code:
            return Response({'error': 'Code required'}, status=status.HTTP_400_BAD_REQUEST)

        code = str(raw_code).replace(' ', '')
        totp = pyotp.TOTP(user.mfa_secret)

        if totp.verify(code, valid_window=1):

            user.is_mfa_enabled = True

            user.save()


            return Response({'message': 'MFA enabled successfully'})


        return Response({'error': 'Invalid code'}, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
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

        tenant = user.profile.tenant
        subscription = getattr(tenant, 'currentsubscription', None)

        refresh = RefreshToken.for_user(user)

        role = None # Initialize the role with a default fallback

        if tenant:
            with schema_context(tenant.schema_name):
                try: role = Employee.objects.get(user=user).role
                
                except Employee.DoesNotExist:
                    return Response(
                        {'error': 'Employee profile not found'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        else:
            if user.is_superuser: role = 'superadmin'


        return Response({
            'message': 'Successfully logged in!',
            'data': {
                'user': user.profile.full_name,
                'tenant': tenant.name if tenant else 'System',
                'role': role,
                'subdomain': tenant.schema_name.replace('tenant_', '') if tenant else None,
                'plan': subscription.plan if subscription else None
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
        raw_code = request.data.get('code')

        if not email or not raw_code:
            return Response(
                {'error': 'Both email and verification code are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)

            if not user.mfa_secret or not user.is_mfa_enabled:
                return Response(
                    {'error': 'MFA is not active for this account'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            code = str(raw_code).replace(' ', '')
            totp = pyotp.totp.TOTP(user.mfa_secret)

            if totp.verify(code):
                profile = getattr(user, 'profile', None)
                tenant = profile.tenant if profile else None
                subscription = getattr(tenant, 'currentsubscription', None)

                refresh = RefreshToken.for_user(user)

                role = None

                if tenant:
                    with schema_context(tenant.schema_name):
                        try: role = Employee.objects.get(user=user).role
                        
                        except Employee.DoesNotExist:
                            return Response(
                                {'error': 'Employee profile not found'},
                                status=status.HTTP_400_BAD_REQUEST
                            )

                else:
                    if user.is_superuser: role = 'superadmin'


                return Response({
                    'message': 'Successfully logged in!',
                    'data': {
                        'user': profile.full_name if profile else user.email,
                        'tenant': tenant.name if tenant else 'System',
                        'role': role,
                        'subdomain': tenant.schema_name.replace('tenant_', '') if tenant else None,
                        'plan': subscription.plan if subscription else None
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

        profile = getattr(user, 'profile', None)
        user_tenant = profile.tenant if profile else None

        role = 'viewer' # Safe fallback


        # 1. If we are running under a tenant schema, query relation directly

        if connection.schema_name != 'public':
            try:
                role = user.employee_profile.role

            except AttributeError:
                pass


        # 2. If we are on the public domain, but the user is associated with a tenant

        elif user_tenant:
            with schema_context(user_tenant.schema_name):
                try:
                    role = Employee.objects.get(user=user).role

                except Employee.DoesNotExist:
                    pass


        # 3. If we are on the public domain and they are a superuser

        else:
            if user.is_superuser:
                role = 'superadmin'


        return Response({
            "identity": {
                "email": user.email,
                "full_name": profile.full_name if profile else None
            },
            "other": {
                "role": role,
                "created_at": user.created_at,
                "is_mfa_enabled": user.is_mfa_enabled
            },
            "tenant": {
                "name": tenant.name if tenant else 'System'
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
