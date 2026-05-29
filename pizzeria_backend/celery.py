import os

from celery import Celery


# 1. Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pizzeria_backend.settings')


# 2. Instantiate the Celery app
app = Celery('pizzeria_backend')


# 3. Read configuration from Django settings using a 'CELERY_' prefix namespace.
app.config_from_object('django.conf:settings', namespace='CELERY')


# 4. Automatically discover background 'tasks.py' modules inside all installed apps.
app.autodiscover_tasks()
