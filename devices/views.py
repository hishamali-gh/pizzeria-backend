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

        # Retrieve the employee model of the active user session
        employee = None
        if request.user.is_authenticated:
            try:
                from employees.models import Employee
                employee = Employee.objects.get(user=request.user)
            except Employee.DoesNotExist:
                pass

        if new_status is not None:
            device.is_on = new_status

        if new_val is not None:
            device.setpoint = new_val

            # Define safety thresholds per device type
            THRESHOLDS = {
                'oven': 450.0,
                'conveyor': 0.8,
                'pump': 15.0,
            }

            limit = THRESHOLDS.get(device.type)

            if limit is not None:
                if new_val > limit:
                    alert_type = f"{device.type.upper()}_THRESHOLD_VIOLATION"
                    
                    # Log a new Alert if no active alert of this type is currently open for the device
                    active_alert = Alert.objects.filter(
                        device=device,
                        type=alert_type,
                        is_acknowledged=False
                    ).exists()

                    if not active_alert:
                        Alert.objects.create(
                            device=device,
                            type=alert_type,
                            threshold=limit,
                            value=new_val,
                            triggered_by=employee,
                            is_acknowledged=False
                        )
                        
                        # Queue async Celery email notifications to all tenant staff members
                        from .tasks import send_tenant_panic_alert
                        from django.db import connection
                        send_tenant_panic_alert.delay(
                            connection.schema_name,
                            device.name,
                            f"Setpoint of {new_val} exceeded the safety limit of {limit}"
                        )
                else:
                    # If setpoint returned to safe limits, auto-acknowledge all active alerts
                    active_alerts = Alert.objects.filter(
                        device=device,
                        is_acknowledged=False
                    )
                    for alert in active_alerts:
                        alert.acknowledge(employee)

        device.save()

        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            f"telemetry_{device.device_id}",
            {
                "type": "device_command",
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


        # 3. Calculate target deviations and command routing

        command = None
        device = data.device

        if device.is_on and not is_on:
            command = 'START'

        elif not device.is_on and is_on:
            command = 'SHUTDOWN'

        response_data = serializer.data
        response_data['command'] = command
        response_data['target_value'] = device.setpoint


        return Response(response_data, status=status.HTTP_200_OK)


class AlertViewSet(ReadOnlyModelViewSet):
    queryset = Alert.objects.all()
    serializer_class = AlertModelSerializer

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        alert = self.get_object()
        
        employee = None
        if request.user.is_authenticated:
            try:
                from employees.models import Employee
                employee = Employee.objects.get(user=request.user)
            except Employee.DoesNotExist:
                pass

        alert.acknowledge(employee)

        return Response({'status': 'alert acknowledged'})
