from django.apps import AppConfig
from celery import app as celery_app


class DjangoGeosourceConfig(AppConfig):
    name = "django_geosource"
