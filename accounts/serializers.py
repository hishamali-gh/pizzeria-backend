from rest_framework import serializers

from django.contrib.auth import get_user_model, authenticate
from django.db import transaction, connection

from django_tenants.utils import schema_context

from billing.models import SubscriptionStatus
from billing.serializers import CurrentSubscription, RazorpayPaymentSerializer
from tenants.models import Tenant, Domain
from tenants.serializers import TenantSerializer
from employees.models import Role, Employee
from .models import UserProfile


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)


    class Meta:
        model = User
        fields = ['email', 'password', 'confirm_password']
        extra_kwargs = {
            'password': {
                'write_only': True
            },
            'email': {
                'validators': []
            }
        }


    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')

        if password != confirm_password:
            raise serializers.ValidationError('Your password inputs do not match')

        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['full_name']


class RegistrationSerializer(serializers.Serializer):
    tenant = TenantSerializer()
    user = UserSerializer()
    profile = UserProfileSerializer()
    payment = RazorpayPaymentSerializer()


    def create(self, validated_data):
        tenant_data = validated_data.pop('tenant')
        user_data = validated_data.pop('user')
        profile_data = validated_data.pop('profile')
        payment_data = validated_data.pop('payment')

        subdomain = tenant_data.get('subdomain').strip().lower().replace('-', '_')

        with transaction.atomic():
            tenant = Tenant.objects.create(
                name=tenant_data.get('name'),
                schema_name=f"tenant_{subdomain}"
            ) # Tenant created

            Domain.objects.create(
                domain=f"{subdomain}.localhost",
                tenant=tenant,
                is_primary=True
            ) # Domain created

            CurrentSubscription.objects.create(
                tenant=tenant,
                plan=payment_data.get('plan'),
                status=SubscriptionStatus.ACTIVE
            ) # CurrentSubscription created; also did SubscriptionAuditLog, via signal

            user_data.pop('confirm_password', None)

            user = User.objects.create_user(
                email=user_data.get('email'),
                password=user_data.get('password')
            ) # User created

            UserProfile.objects.create(
                user=user,
                full_name=profile_data.get('full_name'),
                tenant=tenant
            ) # Profile created

            with schema_context(tenant.schema_name):
                Employee.objects.create(
                    user=user,
                    role=Role.ADMIN
                ) # Employee created

            return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


    def validate(self, attrs):
            email = attrs.get('email')
            password = attrs.get('password')

            if not email or not password:
                raise serializers.ValidationError('Both email and password are required.')

            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )

            if not user:
                raise serializers.ValidationError('Invalid email or password.')

            if not user.is_active:
                raise serializers.ValidationError('This account is disabled.')

            attrs['user'] = user

            return attrs
