import os
from unittest import mock

from django.core.management import call_command
from django.test import TestCase
from rest_framework.exceptions import MethodNotAllowed

from django_geosource.models import GeoJSONSource, GeometryTypes


class ResyncAllSourcesTestCase(TestCase):
    def setUp(self):
        self.source = GeoJSONSource.objects.create(
            name="test",
            geom_type=GeometryTypes.Point.value,
            file=os.path.join(os.path.dirname(__file__), "data", "test.geojson"),
        )

    def test_resync_all_sources(self):
        def side_effect(method, list, **kwargs):
            return "Task"

        with mock.patch(
            "django_geosource.celery.app.send_task", side_effect=side_effect
        ) as mocked:
            with mock.patch(
                "django_geosource.mixins.CeleryCallMethodsMixin.update_status",
                return_value=False,
            ):
                call_command("resync_all_sources")
        mocked.assert_called_once()

    def test_resync_all_sources_sync(self):

        with mock.patch("django_geosource.models.GeoJSONSource.refresh_data") as mocked:
            call_command("resync_all_sources", sync=True)

        mocked.assert_called_once()

    def test_resync_source(self):
        def side_effect(method, list, **kwargs):
            return "Task"

        with mock.patch(
            "django_geosource.celery.app.send_task", side_effect=side_effect
        ) as mocked:
            with mock.patch(
                "django_geosource.mixins.CeleryCallMethodsMixin.update_status",
                return_value=False,
            ):
                call_command("resync_source", pk=self.source.id)
        mocked.assert_called_once()

    def test_resync_all_sources_sync(self):

        with mock.patch("django_geosource.models.GeoJSONSource.refresh_data") as mocked:
            call_command("resync_all_sources", sync=True)

        mocked.assert_called_once()

    def test_resync_source_sync(self):

        with mock.patch("django_geosource.models.GeoJSONSource.refresh_data") as mocked:
            call_command("resync_source", pk=self.source.id, sync=True)

        mocked.assert_called_once()

    def test_resync_all_sources_fail(self):
        with mock.patch("django_geosource.mixins.CeleryCallMethodsMixin.update_status"):
            with mock.patch(
                "django_geosource.mixins.CeleryCallMethodsMixin.can_sync",
                new_callable=mock.PropertyMock,
                return_value=False,
            ):
                with self.assertRaisesRegexp(
                    MethodNotAllowed,
                    'Method "One job is still running on this source" not allowed.',
                ):
                    call_command("resync_all_sources")

    def test_resync_all_sources_fail_force(self):
        def side_effect(method, list, **kwargs):
            return "Task"

        with mock.patch(
            "django_geosource.celery.app.send_task", side_effect=side_effect
        ) as mocked:
            with mock.patch(
                "django_geosource.mixins.CeleryCallMethodsMixin.update_status"
            ):
                with mock.patch(
                    "django_geosource.mixins.CeleryCallMethodsMixin.can_sync",
                    new_callable=mock.PropertyMock,
                    return_value=False,
                ):
                    call_command("resync_all_sources", force=True)
        mocked.assert_called_once()
