from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CurrentSubscription, SubscriptionAuditLog


@receiver(post_save, sender=CurrentSubscription)
def log_subscription(sender, instance, created, **kwargs):
    SubscriptionAuditLog.objects.create(
        tenant=instance.tenant,
        plan=instance.plan,
        status=instance.status
    )

    print(f"AUDIT LOG: {'CREATED' if created else 'UPDATED'} subscription for {instance.tenant.name}")
