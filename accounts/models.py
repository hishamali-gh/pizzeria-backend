import uuid

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

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


    def __str__(self):
        tenant_name = self.tenant.name if self.tenant else "System"

        return f"{self.full_name} - {tenant_name}"
