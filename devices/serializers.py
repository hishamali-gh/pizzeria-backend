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
    triggered_by = serializers.StringRelatedField(read_only=True)
    acknowledged_by = serializers.StringRelatedField(read_only=True)

    device_id = serializers.SlugRelatedField(
        source='device',
        slug_field='device_id',
        read_only=True
    )

    class Meta:
        model = Alert
        fields = [
            'id', 'device', 'device_id', 'type', 'threshold', 'value',
            'is_acknowledged', 'acknowledged_by', 'acknowledged_at',
            'triggered_by', 'created_at'
        ]
        extra_kwargs = {
            'device': {'read_only': True},
            'type': {'read_only': True},
            'threshold': {'read_only': True},
            'value': {'read_only': True},
        }
