from .celery import app as celery_app

class AsyncMethodsMixin:

    def run_async_method(self, method):
        return celery_app.send_task(
            'django_geosource.celery.tasks.run_model_object_method',
            (self._meta.app_label, self.__class__.__name__, self.pk, method))
