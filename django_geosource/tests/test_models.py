import json
import os
from io import StringIO
from unittest import mock

from django.conf import settings
from django.test import TestCase
from django_geosource.models import (
    CommandSource,
    CSVSource,
    Field,
    GeoJSONSource,
    GeometryTypes,
    PostGISSource,
    ShapefileSource,
    Source,
    WMTSSource,
)
from geostore.models import Layer


class MockBackend(object):
    def __init__(self, *args, **kwargs):
        pass

    def get(self, id):
        return """{"result": {"%s": "NOT OK!"}}""" % id

    def get_key_for_task(self, id):
        return id


class MockAsyncResult(object):
    def __init__(self, task_id, *args, **kwargs):
        self.backend = MockBackend()

    @property
    def date_done(self):
        return "DONE"

    @property
    def state(self):
        return "ENDED"


class MockAsyncResultSucess(MockAsyncResult):
    @property
    def result(self):
        return "OK!"

    def successful(self):
        return True

    def failed(self):
        return False


class MockAsyncResultFail(MockAsyncResult):
    @property
    def id(self):
        return 1

    @property
    def result(self):
        return {self.id: "NOT OK!"}

    def successful(self):
        return False

    def failed(self):
        return True


class ModelSourceTestCase(TestCase):
    def setUp(self):
        self.source = Source.objects.create(
            name="Toto", geom_type=GeometryTypes.LineString.value
        )
        self.geojson_source = GeoJSONSource.objects.create(
            name="Titi",
            geom_type=GeometryTypes.Point.value,
            file=os.path.join(os.path.dirname(__file__), "data", "test.geojson"),
        )

    def test_source_str(self):
        self.assertEqual(str(self.source), "Toto - Source")

    def test_other_source_str(self):
        self.assertEqual(str(self.geojson_source), "Titi - GeoJSONSource")

    def test_source_type(self):
        self.assertEqual(self.source.type, self.source.__class__)

    def test_query_filter(self):
        results = Source.objects.all()
        self.assertEqual(len(results), 2)

        results = Source.objects.filter(geom_type=GeometryTypes.LineString.value)
        self.assertEqual(len(results), 1)

    def test_geojsonsource_type(self):
        self.assertEqual(self.geojson_source.type, self.geojson_source.__class__)

    def test_wrong_identifier_refresh(self):
        self.geojson_source.id_field = "wrong_identifier"
        self.geojson_source.save()
        with self.assertRaisesRegexp(
            Exception, "Can't find identifier field in one or more records"
        ):
            self.geojson_source.refresh_data()

    def test_delete(self):
        self.geojson_source.refresh_data()
        self.assertEqual(Layer.objects.count(), 1)
        self.geojson_source.delete()
        self.assertEqual(Layer.objects.count(), 0)

    @mock.patch("django_geosource.models.AsyncResult", new=MockAsyncResultSucess)
    def test_get_status(self):
        self.geojson_source.task_id = 1
        self.geojson_source.save()
        self.geojson_source.get_status()
        self.assertEqual(
            {"state": "ENDED", "result": "OK!", "done": "DONE"},
            self.geojson_source.get_status(),
        )

    @mock.patch("django_geosource.models.AsyncResult", new=MockAsyncResultFail)
    def test_get_status_fail(self):
        self.geojson_source.task_id = 1
        self.geojson_source.save()
        self.assertEqual(
            {"state": "ENDED", "done": "DONE", "1": "NOT OK!"},
            self.geojson_source.get_status(),
        )


class ModelFieldTestCase(TestCase):
    def test_field_str(self):
        source = Source.objects.create(name="Toto", geom_type=GeometryTypes.Point.value)
        field = Field.objects.create(source=source, name="tutu")
        self.assertEqual(str(field), "tutu (Toto - 5)")


class ModelPostGISSourceTestCase(TestCase):
    def setUp(self):
        self.geom_field = "geom"
        self.source = PostGISSource.objects.create(
            name="Toto", geom_type=GeometryTypes.Point.value, geom_field=self.geom_field
        )

    def test_source_geom_attribute(self):
        self.assertEqual(self.geom_field, self.source.SOURCE_GEOM_ATTRIBUTE)

    @mock.patch("psycopg2.connect", return_value=mock.Mock())
    def test_test_get_records(self, mock_con):
        self.source._get_records(1)
        mock_con.assert_called_once()


class ModelGeoJSONSourceTestCase(TestCase):
    def test_get_file_as_dict(self):
        source = GeoJSONSource.objects.create(
            name="Titi",
            geom_type=GeometryTypes.Point.value,
            file=os.path.join(os.path.dirname(__file__), "data", "test.geojson"),
        )
        self.assertEqual(
            source.get_file_as_dict(),
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "properties": {"id": 1, "test": 5},
                        "geometry": {
                            "type": "Point",
                            "coordinates": [3.0808067321777344, 45.77488685869771],
                        },
                    }
                ],
            },
        )

    def test_get_file_as_dict_wrong_file(self):
        source = GeoJSONSource.objects.create(
            name="Titi",
            geom_type=GeometryTypes.Point.value,
            file=os.path.join(os.path.dirname(__file__), "data", "bad.geojson"),
        )
        with self.assertRaises(json.decoder.JSONDecodeError):
            source.get_file_as_dict()

    def test_get_records_wrong_geom_file(self):
        source = GeoJSONSource.objects.create(
            name="Titi",
            geom_type=GeometryTypes.Point.value,
            file=os.path.join(os.path.dirname(__file__), "data", "bad_geom.geojson"),
        )
        with self.assertRaises(ValueError) as m:
            source._get_records(1)
        self.assertEqual(
            "One of source's record has bad geometry: {'type': 'LineString', "
            "'coordinates': [3.0808067321777344, 45.77488685869771]}",
            str(m.exception),
        )


class ModelShapeFileSourceTestCase(TestCase):
    def test_get_records(self):
        source = ShapefileSource.objects.create(
            name="Titi",
            geom_type=GeometryTypes.Point.value,
            file=os.path.join(os.path.dirname(__file__), "data", "test.zip"),
        )
        records = source._get_records(1)
        self.assertEqual(records[0]["NOM"], "Trifouilli-les-Oies")
        self.assertEqual(records[0]["Insee"], 99999)
        self.assertEqual(records[0]["_geom_"].geom_typeid, GeometryTypes.Polygon.value)


class ModelCommandSourceTestCase(TestCase):
    def setUp(self):
        self.source = CommandSource.objects.create(
            name="Titi", geom_type=GeometryTypes.Point.value, command="command_test"
        )

    @mock.patch("sys.stdout", new_callable=StringIO)
    def test_refresh_data(self, mocked_stdout):

        self.source.refresh_data()
        self.assertIn("TestFooBarBar", mocked_stdout.getvalue())

    def test_get_records(self):
        self.assertEqual([], self.source._get_records())


class ModelWMTSSourceTestCase(TestCase):
    def setUp(self):
        self.source = WMTSSource.objects.create(
            name="Titi", geom_type=GeometryTypes.Point.value, tile_size=256, minzoom=14,
        )

    def test_get_records(self):
        self.assertEqual([], self.source._get_records())

    def test_get_status(self):
        self.assertEqual({"state": "DONT_NEED"}, self.source.get_status())

    def test_refresh_data(self):
        self.assertEqual({}, self.source.refresh_data())


class ModelCSVSourceTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.base_settings = {
            "encoding": "UTF-8",
            "coordinate_reference_system": "EPSG_4326",
            "field_separator": "semicolon",
            "decimal_separator": "coma",
            "use_header": True,
        }

    def test_get_records_with_two_columns_coordinates(self):
        source_name = os.path.join(
            settings.BASE_DIR, "django_geosource", "tests", "source.csv"
        )
        source = CSVSource.objects.create(
            file=source_name,
            geom_type=0,
            settings={
                **self.base_settings,
                "coordinates_field": "two_columns",
                "longitude_field": "XCOORD",
                "latitude_field": "YCOORD",
            },
        )
        records = source._get_records()
        self.assertEqual(len(records), 6, len(records))

    def test_get_records_with_one_column_coordinates(self):
        source_name = os.path.join(
            settings.BASE_DIR, "django_geosource", "tests", "source_xy.csv"
        )
        source = CSVSource.objects.create(
            file=source_name,
            geom_type=0,
            settings={
                **self.base_settings,
                "coordinates_field": "one_column",
                "latlong_field": "coordxy",
                "coordinates_separator": "coma",
                "coordinates_field_count": "xy",
            },
        )
        records = source._get_records()
        self.assertEqual(len(records), 9, len(records))
