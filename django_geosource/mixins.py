from django_geosource.celery.tasks import run_model_object_method
from rest_framework.exceptions import MethodNotAllowed
from .celery import app as celery_app


class CeleryCallMethodsMixin:

    def update_status(self, task):
        self.status = task.task_id
        self.save()

    def run_async_method(self, method, force=False):
        if self.get_status().get('state') in ('SUCCESS', 'FAILURE', None) or force:
            task_job = celery_app.send_task(
                'django_geosource.celery.tasks.run_model_object_method',
                (self._meta.app_label, self.__class__.__name__, self.pk, method))

            self.update_status(task_job)
            return task_job

        raise MethodNotAllowed('One job is still running on this source')

    def run_sync_method(self, method):
        task_job = run_model_object_method.apply((self._meta.app_label, self.__class__.__name__, self.pk, method, ))
        self.update_status(task_job)
        return task_job
