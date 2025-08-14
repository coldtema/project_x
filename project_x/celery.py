import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project_x.settings')

app = Celery('project_x')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
 