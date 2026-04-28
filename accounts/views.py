from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from accounts.serializers import RegistrationSerializer
from .serializers import LoginSerializer


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



class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})

        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data.get('user')

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
        }, status=status.HTTP_200_OK)
