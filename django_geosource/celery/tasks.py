import logging

from celery import shared_task
from django.apps import apps

logger = logging.getLogger(__name__)


@shared_task()
def run_model_object_method(app, model, pk, method):
    Model = apps.get_app_config(app).get_model(model)
    try:
        obj = Model.objects.get(pk=pk)
        return getattr(obj, method)()
    except Model.DoesNotExist:
        logger.warning(f"{Model}'s object with pk {pk} doesn't exist")

    except AttributeError:
        logger.warning(f"{method} doesn't exist for object {obj}")
    except Exception as e:
        logger.warning(f"An exception occured runing {method} on model {model}'s object with pk {pk}: {e}")
