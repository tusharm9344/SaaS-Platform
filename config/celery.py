import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")

# Read Celery configuration from Django settings.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Automatically discover tasks.py files inside Django apps.
app.autodiscover_tasks()