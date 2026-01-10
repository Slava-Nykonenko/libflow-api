import os
from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "libflow_api.settings")
CELERY_BROKER_URL = "redis://redis:6379/0"

app = Celery("libflow_api")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
