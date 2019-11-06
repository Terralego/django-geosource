from datetime import timedelta
from django.utils.timezone import now
from django_geosource.celery.tasks import run_model_object_method
from rest_framework.exceptions import MethodNotAllowed
from celery import states

from .app_settings import MAX_TASK_RUNTIME
from .celery import app as celery_app


class CeleryCallMethodsMixin:

    DONE_STATUSES = ("SUCCESS", "FAILURE", "NEED_SYNC", None)

    def update_status(self, task):
        self.task_id = task.task_id
        self.task_date = now()
        self.save()

    @property
    def can_sync(self):
        status = self.get_status()

        return status.get("state") in self.DONE_STATUSES or (
            status.get("state") not in self.DONE_STATUSES
            and self.task_date is not None
            and self.task_date < now() - timedelta(hours=MAX_TASK_RUNTIME)
        )

    def run_async_method(self, method, success_state=states.SUCCESS, force=False):
        if self.can_sync or force:
            task_job = celery_app.send_task(
                "django_geosource.celery.tasks.run_model_object_method",
                (self._meta.app_label, self.__class__.__name__, self.pk, method),
            )

            self.update_status(task_job)
            return task_job

        raise MethodNotAllowed("One job is still running on this source")

    def run_sync_method(self, method, success_state=states.SUCCESS):
        task_job = run_model_object_method.apply(
            (
                self._meta.app_label,
                self.__class__.__name__,
                self.pk,
                method,
                success_state,
            )
        )
        self.update_status(task_job)
        return task_job
