import uuid

from datetime import timedelta

from django.db import models
from django.conf import settings
from django.utils import timezone


class Role(models.TextChoices):
    SUPERADMIN = 'superadmin', 'Super Admin'
    ADMIN = 'admin', 'Admin'
    WORKER = 'worker', 'Worker'
    VIEWER = 'viewer', 'Viewer'


class Employee(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='employee_profile')
    role = models.TextField(choices=Role.choices, default=Role.VIEWER)


    def __str__(self):
        if hasattr(self.user, 'profile'):
            return self.user.profile.full_name

        return self.user.email


class EmployeeInvitation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField()
    role = models.CharField(max_length=20) 

    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    is_used = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)


    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(hours=24)

    def __str__(self):
        return f"Invite for {self.email} - {self.role}"
