import json
import os
from django.test import TestCase

from django_geosource.models import (
    PostGISSource,
    Source,
    Field,
    GeometryTypes,
    GeoJSONSource,
)


class ModelSourceTestCase(TestCase):
    def test_source_str(self):
        source = Source.objects.create(name="Toto", geom_type=GeometryTypes.Point.value)
        self.assertEqual(str(source), "Toto - Source")

    def test_other_source_str(self):
        source = GeoJSONSource.objects.create(name="Titi", geom_type=GeometryTypes.Point.value)
        self.assertEqual(str(source), "Titi - GeoJSONSource")


class ModelFieldTestCase(TestCase):
    def test_field_str(self):
        source = Source.objects.create(name="Toto", geom_type=GeometryTypes.Point.value)
        field = Field.objects.create(source=source, name="tutu")
        self.assertEqual(str(field), "tutu (Toto - 5)")


class ModelPostGISSourceTestCase(TestCase):
    def test_source_geom_attribute(self):
        geom_field = "geom"
        source = PostGISSource.objects.create(name="Toto", geom_type=GeometryTypes.Point.value, geom_field=geom_field)
        self.assertEqual(geom_field, source.SOURCE_GEOM_ATTRIBUTE)


class ModelGeoJSONSourceTestCase(TestCase):
    def test_get_file_as_dict(self):
        source = GeoJSONSource.objects.create(name="Titi", geom_type=GeometryTypes.Point.value,
                                              file=os.path.join(os.path.dirname(__file__), 'data', 'test.geojson'))
        self.assertEqual(source.get_file_as_dict(), {'type': 'FeatureCollection',
                                                     'features':
                                                         [
                                                             {'type': 'Feature',
                                                              'properties': {'id': 1, 'test': 5},
                                                              'geometry': {'type': 'Point',
                                                                           'coordinates': [3.0808067321777344,
                                                                                           45.77488685869771]
                                                                           }
                                                              }
                                                         ]
                                                     })

    def test_get_file_as_dict_wrong_file(self):
        source = GeoJSONSource.objects.create(name="Titi", geom_type=GeometryTypes.Point.value,
                                              file=os.path.join(os.path.dirname(__file__), 'data', 'bad.geojson'))
        with self.assertRaises(json.decoder.JSONDecodeError):
            source.get_file_as_dict()

    def test_get_records_wrong_geom_file(self):
        source = GeoJSONSource.objects.create(name="Titi", geom_type=GeometryTypes.Point.value,
                                              file=os.path.join(os.path.dirname(__file__), 'data', 'bad_geom.geojson'))
        with self.assertRaises(ValueError) as m:
            source._get_records(1)
        self.assertEqual("One of source's record has bad geometry: {'type': 'LineString', "
                         "'coordinates': [3.0808067321777344, 45.77488685869771]}", str(m.exception))
