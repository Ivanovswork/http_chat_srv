import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'http_chat.settings')
app = Celery('http_chat')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()