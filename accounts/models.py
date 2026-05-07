import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings

import pyotp


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Industrial operators must have a valid email.')

        email = self.normalize_email(email)

        user = self.model(email=email, **extra_fields)

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    username = None
    email = models.EmailField(unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []


    # MFA CONFIG.

    is_mfa_enabled = models.BooleanField(default=False)
    mfa_secret = models.CharField(max_length=32, blank=True, null=True)


    def generate_mfa_secret(self):
        self.mfa_secret = pyotp.random_base32()

        self.save()

    def get_totp_uri(self):
        profile_tenant = self.profile.tenant.name if hasattr(self, 'profile') and self.profile.tenant else 'System Admin'
        
        return pyotp.totp.TOTP(self.mfa_secret).provisioning_uri(
            name=self.email,
            issuer_name=f"Pizzeria - {profile_tenant}"
        )


    def __str__(self):
        return self.email


class UserProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.TextField()
    tenant = models.ForeignKey(settings.TENANT_MODEL, on_delete=models.CASCADE, related_name='profiles', null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        tenant_name = self.tenant.name if self.tenant else 'System'

        return f'{self.full_name} - {tenant_name}'
