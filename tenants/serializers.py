from rest_framework import serializers

from django.contrib.auth import get_user_model

from .models import Tenant


User = get_user_model()


class TenantSerializer(serializers.ModelSerializer):
    subdomain = serializers.CharField(write_only=True)


    class Meta:
        model = Tenant
        fields = ['name', 'subdomain']
