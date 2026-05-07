import uuid

from django_tenants.models import TenantMixin, DomainMixin

from django.db import models


class Tenant(TenantMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.TextField()

    # There's also a hidden field 'schema_name', too.

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    auto_create_schema = True
    auto_drop_schema = True


class Domain(DomainMixin):
    pass
