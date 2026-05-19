from rest_framework import serializers

from .models import EmployeeInvitation


class EmployeeInvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeInvitation
        fields = ['email', 'role']
