from rest_framework import serializers

from .models import Device, Telemetry, Alert


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['device_id', 'name', 'type']


class TelemetryIngestionSerializer(serializers.ModelSerializer):
    device = serializers.SlugRelatedField(
        slug_field='device_id',
        queryset=Device.objects.all()
    )

    
    class Meta:
        model = Telemetry
        fields = ['device', 'value', 'is_on']


    def create(self, validated_data):
        device = validated_data.get('device')
        device.is_on = validated_data.get('is_on')

        device.save()

        return Telemetry.objects.create(**validated_data)
   

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
