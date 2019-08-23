from celery import Celery

app = Celery('django_geosource')

app.config_from_object('django.conf:settings', namespace='CELERY')

from django.conf import settings

app.autodiscover_tasks(['django_geosource.celery', ])
