import uuid

from django.db import models

from tenants.models import Tenant


class PlanType(models.TextChoices):
    BASE = 'BASE', 'Base'
    PLUS = 'PLUS', 'Plus'
    PRO = 'PRO', 'Pro'


class SubscriptionStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Active'
    PAST_DUE = 'PAST_DUE', 'Past Due'
    CANCELLED = 'CANCELLED', 'Cancelled'


class CurrentSubscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE)
    
    plan = models.CharField(max_length=20, choices=PlanType.choices)
    status = models.CharField(max_length=20, choices=SubscriptionStatus.choices)

    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"CURRENT: {self.tenant.name} - {self.plan}"


class SubscriptionAuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(Tenant, related_name='subscriptions', on_delete=models.CASCADE)

    plan = models.CharField(max_length=20, choices=PlanType.choices)
    status = models.CharField(max_length=20, choices=SubscriptionStatus.choices)

    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"LOG: {self.tenant.name} changed to {self.plan} at {self.created_at}"
