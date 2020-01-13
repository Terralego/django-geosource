from datetime import datetime
import subprocess
from unittest import mock

from django.test import TestCase
from django.utils import timezone

from django_geosource.celery.schedulers import GeosourceScheduler, SourceEntry
from django_geosource.models import PostGISSource, GeometryTypes

from django_geosource.celery import app as celery_app

from rest_framework.exceptions import MethodNotAllowed

import logging


class SourceEntrySchedulerTestCase(TestCase):
    def setUp(self):
        self.source = PostGISSource.objects.create(name="First Source",
                                                   db_host="localhost",
                                                   db_name="dbname",
                                                   db_username="username",
                                                   query="SELECT 1",
                                                   geom_field="geom",
                                                   refresh=-1,
                                                   geom_type=GeometryTypes.LineString.value)

    def test_celery_source_entry_is_due_refresh_infinite(self):
        entry = SourceEntry(self.source, app=celery_app)
        self.assertEqual(entry.is_due().is_due, False)
        self.assertEqual(entry.is_due().next, 600)

    def test_celery_source_entry_is_due_refresh(self):
        self.source.refresh = 1
        self.source.save()
        entry = SourceEntry(self.source, app=celery_app)
        self.assertEqual(entry.is_due().is_due, False)
        self.assertEqual(entry.is_due().next, 10)

    @mock.patch('django.utils.timezone.now')
    def test_celery_source_entry_is_due_refresh_before_now(self, mock_timezone):
        dt = datetime(2099, 1, 1, tzinfo=timezone.utc)
        mock_timezone.return_value = dt
        self.source.refresh = 1
        self.source.save()
        entry = SourceEntry(self.source, app=celery_app)
        self.assertEqual(entry.is_due().is_due, True)
        self.assertEqual(entry.is_due().next, 10)

    def test_celery_source_entry_next(self):
        entry = SourceEntry(self.source, app=celery_app)
        self.assertEqual(str(entry.__next__(datetime(2099, 1, 1, tzinfo=timezone.utc)).source),
                         "First Source - PostGISSource")

    def test_celery_source_entry_run_task(self):
        entry = SourceEntry(self.source, app=celery_app)
        logging.disable(logging.ERROR)
        with mock.patch('django_geosource.mixins.CeleryCallMethodsMixin.can_sync',
                        new_callable=mock.PropertyMock, return_value=False):
            with mock.patch('django_geosource.mixins.CeleryCallMethodsMixin.run_async_method',
                            side_effect=MethodNotAllowed('Test')) as mocked:
                entry.run_task()
        mocked.assert_called_once()
