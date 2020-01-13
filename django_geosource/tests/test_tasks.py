import os
import logging
from unittest import mock

from django.contrib.auth.models import Group
from django.test import TestCase

from celery.exceptions import Ignore

from django_geosource.celery.tasks import run_model_object_method
from django_geosource.models import GeoJSONSource, GeometryTypes

from geostore.models import Feature, Layer


class TaskTestCase(TestCase):
    def setUp(self):
        self.group = Group.objects.create(name="Group")
        self.element = GeoJSONSource.objects.create(
            name="test",
            geom_type=GeometryTypes.Point.value,
            file=os.path.join(os.path.dirname(__file__), 'data', 'test.geojson'),
            settings={"groups": [self.group.pk]}
        )

    def test_task_refresh_data_method(self):
        with self.assertRaises(Ignore):
            run_model_object_method(self.element._meta.app_label, self.element._meta.model_name,
                                    self.element.pk, 'refresh_data')
        self.assertEqual(Layer.objects.count(), 1)
        self.assertEqual(Feature.objects.count(), 1)
        self.assertEqual(Feature.objects.first().properties, {'id': 1, 'test': 5})
        self.assertEqual(Layer.objects.first().authorized_groups.first().name, "Group")

    def test_task_refresh_data_method_wrong_pk(self):
        logging.disable(logging.WARNING)
        with self.assertRaises(Ignore):
            run_model_object_method(self.element._meta.app_label, self.element._meta.model_name,
                                    99999, 'refresh_data')
        self.assertEqual(Layer.objects.count(), 0)

    def test_task_wrong_method(self):
        logging.disable(logging.ERROR)
        with self.assertRaises(Ignore):
            run_model_object_method(self.element._meta.app_label, self.element._meta.model_name,
                                    self.element.pk, 'bad_method')
        self.assertEqual(Layer.objects.count(), 0)

    @mock.patch("django_geosource.models.Source.objects")
    def test_task_good_method_error(self, mock_source):
        mock_source.get.side_effect = ValueError
        logging.disable(logging.ERROR)
        with self.assertRaises(Ignore):
            run_model_object_method(self.element._meta.app_label, self.element._meta.model_name,
                                    self.element.pk, 'refresh_data')
        self.assertEqual(Layer.objects.count(), 0)
