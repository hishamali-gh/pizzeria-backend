from channels.layers import get_channel_layer

from asgiref.sync import async_to_sync

from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status

from django.utils import timezone

from .serializers import DeviceSerializer, TelemetryIngestionSerializer, AlertModelSerializer
from .models import Device, Alert


class DeviceViewSet(ModelViewSet):
    serializer_class = DeviceSerializer
    queryset = Device.objects.all()

    @action(detail=True, methods=['patch'])
    def control(self, request, pk=None):
        device = self.get_object()

        new_val = request.data.get('last_value')
        new_status = request.data.get('is_on')

        if new_status is not None:
            device.is_on = new_status

        device.save()

        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            f"telemetry_{device.device_id}",
            {
                "type": "device_command", # The simulator must listen for this type
                "value": new_val if new_val is not None else 0.0,
                "is_on": device.is_on
            }
        )

        return Response({
            "status": "COMMAND_DISPATCHED",
            "device_id": device.device_id,
            "setpoint": new_val
        })


class TelemetryIngestionAPIView(APIView):
    def post(self, request):
        serializer = TelemetryIngestionSerializer(data=request.data)
        
        serializer.is_valid(raise_exception=True)


        # 1. Save to the PostgreSQL "Historian"

        data = serializer.save()
        
        device_id = data.device.device_id
        value = request.data.get('value')
        is_on = request.data.get('is_on')


        # 2. Trigger the Broadcast to the "Nervous System" (Redis)

        channel_layer = get_channel_layer()


        # We "shout" into the room specifically named after this device.

        async_to_sync(channel_layer.group_send)(
            f"telemetry_{device_id}", 
            {
                "type": "telemetry_message", # This must match the method name in consumers.py.
                "value": value,
                "status": is_on
            }
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AlertViewSet(ReadOnlyModelViewSet):
    queryset = Alert.objects.all()
    serializer_class = AlertModelSerializer

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        alert = self.get_object()
        
        alert.acknowledge(request.user)

        return Response({'status': 'alert acknowledged'})
