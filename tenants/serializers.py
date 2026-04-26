from rest_framework import serializers

from django.db import transaction
from django.contrib.auth import get_user_model

from billing.models import SubscriptionStatus
from billing.serializers import CurrentSubscription, SubscriptionSerializer
from accounts.models import Role
from accounts.serializers import UserSerializer
from .models import Tenant


User = get_user_model()


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ['name', 'subdomain']


class RegistrationSerializer(serializers.Serializer):
    tenant = TenantSerializer()
    user = UserSerializer()
    subscription = SubscriptionSerializer()


    def create(self, validated_data):
        tenant_data = validated_data.pop('tenant')
        user_data = validated_data.pop('user')
        subscription_data = validated_data.pop('subscription')

        with transaction.atomic():
            tenant = Tenant.objects.create(**tenant_data)

            CurrentSubscription.objects.create(
                tenant=tenant,
                plan=subscription_data.get('plan'),
                status=SubscriptionStatus.ACTIVE
            )

            user_data.pop('confirm_password', None)

            user = User.objects.create_user(
                tenant=tenant,
                role=Role.ADMIN,
                **user_data
            )

            return user
