from datetime import datetime
from unittest import mock

from django.test import TestCase
from django.utils import timezone
from django_geosource.models import GeometryTypes, PostGISSource, GeoJSONSource
from django_geosource.periodics import auto_refresh_source
import os


class PeriodicsTestCase(TestCase):
    def setUp(self):
        self.geosource = GeoJSONSource.objects.create(
            name="test",
            geom_type=GeometryTypes.Point.value,
            file=os.path.join(os.path.dirname(__file__), "data", "test.geojson"),
        )
        self.source = PostGISSource.objects.create(
            name="First Source",
            db_host="localhost",
            db_name="dbname",
            db_username="username",
            query="SELECT 1",
            geom_field="geom",
            refresh=-1,
            last_refresh=datetime(2020, 1, 1, tzinfo=timezone.utc),
            geom_type=GeometryTypes.LineString.value,
        )
        self.source2 = PostGISSource.objects.create(
            name="Second Source",
            db_host="localhost",
            db_name="dbname",
            db_username="username",
            query="SELECT 1",
            geom_field="geom",
            refresh=60 * 24 * 3,
            last_refresh=datetime(2020, 1, 1, tzinfo=timezone.utc),
            geom_type=GeometryTypes.LineString.value,
        )

    @mock.patch("django.utils.timezone.now")
    def test_should_refresh(self, mock_timezone):
        dt = datetime(2099, 1, 1, tzinfo=timezone.utc)
        mock_timezone.return_value = dt

        self.assertEqual(self.source.should_refresh(), False)
        self.assertEqual(self.geosource.should_refresh(), False)

        dt = datetime(2020, 1, 2, tzinfo=timezone.utc)
        mock_timezone.return_value = dt

        self.assertEqual(self.source2.should_refresh(), False)

        dt = datetime(2020, 1, 10, tzinfo=timezone.utc)
        mock_timezone.return_value = dt

        self.assertEqual(self.source2.should_refresh(), True)

    @mock.patch("django.utils.timezone.now")
    def test_auto_refresh(self, mock_timezone):

        with mock.patch(
            "django_geosource.models.Source._refresh_data"
        ) as mocked, mock.patch(
            "django_geosource.mixins.CeleryCallMethodsMixin.update_status",
            return_value=False,
        ):

            dt = datetime(2020, 1, 2, tzinfo=timezone.utc)
            mock_timezone.return_value = dt
            auto_refresh_source()

            mocked.assert_not_called()

        with mock.patch(
            "django_geosource.models.Source._refresh_data"
        ) as mocked2, mock.patch(
            "django_geosource.mixins.CeleryCallMethodsMixin.update_status",
            return_value=False,
        ):

            dt = datetime(2020, 1, 10, tzinfo=timezone.utc)
            mock_timezone.return_value = dt
            auto_refresh_source()

            mocked2.assert_called_once()

        with mock.patch(
            "django_geosource.models.Source._refresh_data"
        ) as mocked2, mock.patch(
            "django_geosource.mixins.CeleryCallMethodsMixin.update_status",
            return_value=False,
        ):

            dt = datetime(2020, 1, 10, tzinfo=timezone.utc)
            mock_timezone.return_value = dt
            auto_refresh_source()

            mocked2.assert_not_called()
