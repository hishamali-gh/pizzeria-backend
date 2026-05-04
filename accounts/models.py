import uuid

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings

import pyotp

from tenants.models import Tenant


class Role(models.TextChoices):
    SUPERADMIN = 'SUPERADMIN', 'Super Admin'
    ADMIN = 'ADMIN', 'Admin'
    WORKER = 'WORKER', 'Worker'
    VIEWER = 'VIEWER', 'Viewer'


class UserManager(BaseUserManager):
    def create_user(self, full_name, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Must provide an email address')

        user = self.model(
            full_name=full_name.strip().title(),
            email=self.normalize_email(email),
            **extra_fields
        )

        user.set_password(password)

        user.save(using=self._db)

        return user


    def create_superuser(self, full_name, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('tenant') is None:
            extra_fields.setdefault('role', Role.SUPERADMIN)

        else:
            extra_fields.setdefault('role', Role.ADMIN)

        return self.create_user(full_name, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    full_name = models.TextField()
    email = models.EmailField(unique=True)

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='users', null=True)
    role = models.CharField(max_length=20, choices=Role.choices)

    is_active = models.BooleanField(default=True)

    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']


    # MFA CONFIG.

    is_mfa_enabled = models.BooleanField(default=False)

    mfa_secret = models.CharField(max_length=32, blank=True, null=True)


    def generate_mfa_secret(self):
        self.mfa_secret = pyotp.random_base32()

        self.save()


    def get_totp_uri(self):
        return pyotp.totp.TOTP(self.mfa_secret).provisioning_uri(
            name=self.email,
            issuer_name=f"Pizzeria - {self.tenant.name if self.tenant else 'System Admin'}"
        )


    def __str__(self):
        tenant_name = self.tenant.name if self.tenant else "System"

        return f"{self.full_name} - {tenant_name}"


class UserTenantMapper(models.Model):
    email = models.EmailField(unique=True)
    tenant = models.ForeignKey(settings.TENANT_MODEL, related_name='tenant_mappings', on_delete=models.CASCADE) # The 'settings.TENANT_MODEL' option is a lazy relationship definition, since hard-coded relationship is error-prone, especially in this situation. (We can also do this by the format "app_labe.ModelName" (as a string), but since we have configured it already in the settings...)


    def __str__(self):
        return f"{self.email} - {self.tenant}"
