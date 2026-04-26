from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import connection
from django.core.management import call_command

from psycopg2 import sql

from .models import Tenant


@receiver(post_save, sender=Tenant)
def define_tenant_schema(sender, instance, created, **kwargs):
    if created:
        schema_name = f"{instance.subdomain.replace('-', '_').lower()}"

        with connection.cursor() as cursor:
            cursor.execute(
                sql.SQL('CREATE SCHEMA IF NOT EXISTS {}').format(sql.Identifier(schema_name))
            )

            # cursor.execute(
            #     sql.SQL('SET search_path TO {}').format(sql.Identifier(schema_name))
            # )

            # try:
            #     call_command('migrate', interactive=False)

            # finally:
            #     cursor.execute('SET search_path TO public')
