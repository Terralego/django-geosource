import os
from unittest import mock

from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import override_settings
from rest_framework.exceptions import MethodNotAllowed
from celery import current_app as celery
from celery.exceptions import Ignore

from django_geosource.celery.tasks import run_model_object_method
from django_geosource.models import GeoJSONSource, GeometryTypes

from geostore.models import Feature, Layer


class ResyncAllSourcesTestCase(TestCase):
    def test_refresh_data(self):
        group = Group.objects.create(name="Group")
        element = GeoJSONSource.objects.create(
            name="test", geom_type=GeometryTypes.Point.value,
            file=os.path.join(os.path.dirname(__file__), 'data', 'test.geojson'),
            settings={"groups": [group.pk]}
        )
        with self.assertRaises(Ignore):
            run_model_object_method(element._meta.app_label, element._meta.model_name, element.pk, 'refresh_data')
        self.assertEqual(Layer.objects.count(), 1)
        self.assertEqual(Feature.objects.count(), 1)
        self.assertEqual(Feature.objects.first().properties, {'id': 1, 'test': 5})
        self.assertEqual(Layer.objects.first().authorized_groups.first().name, "Group")

    def test_resync_all_sources(self):
        def side_effect(method, list, **kwargs):
            return "Task"
        GeoJSONSource.objects.create(
            name="test", geom_type=GeometryTypes.Point.value,
            file=os.path.join(os.path.dirname(__file__), 'data', 'test.geojson')
        )
        with mock.patch('django_geosource.celery.app.send_task',
                        side_effect=side_effect) as mocked:
            with mock.patch('django_geosource.mixins.CeleryCallMethodsMixin.update_status', return_value=False):
                call_command('resync_all_sources')

    def test_resync_all_sources_fail(self):
        GeoJSONSource.objects.create(
            name="test", geom_type=GeometryTypes.Point.value,
            file=os.path.join(os.path.dirname(__file__), 'data', 'test.geojson')
        )
        with mock.patch('django_geosource.mixins.CeleryCallMethodsMixin.update_status'):
            with mock.patch('django_geosource.mixins.CeleryCallMethodsMixin.can_sync',
                            new_callable=mock.PropertyMock, return_value=False) as mock_sync:
                with self.assertRaisesRegexp(MethodNotAllowed,
                                             'Method "One job is still running on this source" not allowed.'):
                    call_command('resync_all_sources')

    def test_resync_all_sources_fail_force(self):
        def side_effect(method, list, **kwargs):
            return "Task"
        GeoJSONSource.objects.create(
            name="test", geom_type=GeometryTypes.Point.value,
            file=os.path.join(os.path.dirname(__file__), 'data', 'test.geojson')
        )
        with mock.patch('django_geosource.celery.app.send_task',
                        side_effect=side_effect) as mocked:
            with mock.patch('django_geosource.mixins.CeleryCallMethodsMixin.update_status'):
                with mock.patch('django_geosource.mixins.CeleryCallMethodsMixin.can_sync',
                                new_callable=mock.PropertyMock, return_value=False) as mock_sync:
                    call_command('resync_all_sources', force=True)
        mocked.assert_called_once()
