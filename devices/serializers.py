from rest_framework import serializers

from .models import Device, Telemetry, Alert


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['id', 'device_id', 'name', 'type', 'is_on', 'setpoint']


class TelemetryIngestionSerializer(serializers.ModelSerializer):
    device = serializers.SlugRelatedField(
        slug_field='device_id',
        queryset=Device.objects.all()
    )

    
    class Meta:
        model = Telemetry
        fields = ['device', 'value', 'is_on']
   

class AlertModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        exclude = ['id', 'created_at']
        extra_kwargs = {
            'device': {'read_only': True},
            'type': {'read_only': True},
            'threshold': {'read_only': True},
            'value': {'read_only': True},
        }
