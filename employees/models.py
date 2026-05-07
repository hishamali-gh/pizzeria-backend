import uuid

from django.db import models
from django.conf import settings


class Role(models.TextChoices):
    SUPERADMIN = 'SUPERADMIN', 'Super Admin'
    ADMIN = 'ADMIN', 'Admin'
    WORKER = 'WORKER', 'Worker'
    VIEWER = 'VIEWER', 'Viewer'


class Employee(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='employee_profile')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.VIEWER)


    def __str__(self):
        if hasattr(self.user, 'profile'):
            return self.user.profile.full_name

        return self.user.email
