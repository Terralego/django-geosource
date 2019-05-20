from .celery import app as celery_app
from django_geosource.celery.tasks import run_model_object_method

class CeleryCallMethodsMixin:

    def run_async_method(self, method):
        return celery_app.send_task(
            'django_geosource.celery.tasks.run_model_object_method',
            (self._meta.app_label, self.__class__.__name__, self.pk, method))

    def run_sync_method(self, method):
        return run_model_object_method.apply((self._meta.app_label, self.__class__.__name__, self.pk, method, ))
