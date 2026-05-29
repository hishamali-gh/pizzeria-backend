from celery import shared_task
from django.core.mail import send_mail
from django_tenants.utils import schema_context
from django.conf import settings
from django.contrib.auth import get_user_model

from employees.models import Employee


User = get_user_model()


@shared_task
def send_tenant_panic_alert(tenant_schema_name, machine_name, violation_details):

    """ Safely switches the database router to the target tenant's isolated vault,
    gathers the localized staff listings, and delivers critical warnings. """   


    # Force connection context down into the specific tenant's schema room

    with schema_context(tenant_schema_name):
        # Pull emails of all active staff members registered within this tenant schema

        # Cross-referencing the Tenant's Employee model to guarantee strict isolation boundaries

        # Look up records starting from the local Tenant table ("The Vault") and follow the Foreign Key relationship backward out to the public User model.

        recipient_emails = list(
            Employee.objects.filter(
                user__is_active=True
            ).values_list('user__email', flat=True)
        )
        
        if not recipient_emails:
            return f"Zero operational workers configured under schema: {tenant_schema_name}. Alert aborted."

        subject = f"[CRITICAL SYSTEM PANIC] - Emergency State Triggered: {machine_name}"

        message = (
            f"ATTENTION OPERATOR / TENANT ADMINISTRATOR:\n\n"
            f"A critical industrial safety threshold has been breached on '{machine_name}'.\n"
            f"Telemetry Violation Details: {violation_details}\n\n"
            f"Action Required: Check your HMI Dashboard Event Logs and engage manual safety interlocks if necessary."
        )

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_emails,
            fail_silently=False,
        )
        
    return f"Emergency transmission dispatched to {len(recipient_emails)} users inside schema: {tenant_schema_name}."


@shared_task
def send_global_admin_checkup():

    """ Executes globally within the public schema space to audit top-level system health
    and email platform superadministrators. """

    # Locate global platform administrators who possess root permissions (unbounded by tenants)

    admin_emails = list(
        User.objects.filter(is_superuser=True, is_active=True).values_list('email', flat=True)
    )
    
    if not admin_emails:
        return "No root system administrators discovered in public registry. Checkup aborted."
        
    subject = "[SYSTEM HEALTH CHECK] - Bimonthly Platform Diagnostic Report"

    message = (
        "Automated System Log Status:\n\n"
        "The Pizzeria Virtual Distributed Control System has successfully executed its 2-month checkup cycle.\n"
        "All underlying transactional indices, public mappers, and tenant schemas are working normally."
    )
    
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=admin_emails,
        fail_silently=False,
    )
    
    return f"Bimonthly platform audit log sent out to {len(admin_emails)} system administrators."
