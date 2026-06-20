import uuid

from django.db import models
from django.utils import timezone

from employees.models import Employee


class DeviceType(models.TextChoices):
    OVEN = 'oven', 'Oven'
    CONVEYOR = 'conveyor', 'Conveyor'
    PUMP = 'pump', 'Pump'


class Device(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    device_id = models.TextField(unique=True) # The unique ID from the '--id' argument in your script
    name = models.TextField()
    type = models.CharField(max_length=50, choices=DeviceType.choices)
    is_on = models.BooleanField(default=False)
    setpoint = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.name} ({self.device_id})"


class Telemetry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='readings')
    value = models.FloatField()
    is_on = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at'])
        ]

    def __str__(self):
        return f"{self.device} - {self.value}"


class Alert(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='alerts')
    type = models.TextField()
    threshold = models.FloatField()
    value = models.FloatField()

    triggered_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, related_name='triggered_alerts', null=True, blank=True)

    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey(Employee, on_delete=models.SET_NULL, related_name='acknowledged_alerts', null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        ordering = ['-created_at']


    def acknowledge(self, employee):
        self.is_acknowledged = True
        self.acknowledged_by = employee
        self.acknowledged_at = timezone.now()

        self.save()
    
    def __str__(self):
        return f"{self.device} - {self.type} ({self.value})"
