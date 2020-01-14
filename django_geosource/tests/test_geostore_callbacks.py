from unittest import mock
import os
from django.test import TestCase

from django.contrib.auth.models import Group
from django.contrib.gis.geos import GEOSGeometry
from django_geosource import geostore_callbacks
from django_geosource.models import GeoJSONSource, GeometryTypes

from geostore.models import Feature, Layer


class GeostoreCallBacksTestCase(TestCase):
    def test_layer_callback(self):
        group = Group.objects.create(name="Group")
        source = GeoJSONSource.objects.create(
            name="test",
            geom_type=GeometryTypes.Point.value,
            file=os.path.join(os.path.dirname(__file__), "data", "test.geojson"),
            settings={"groups": [group.pk]},
        )
        layer = geostore_callbacks.layer_callback(source)
        self.assertEqual(layer.authorized_groups.first().name, "Group")

    def test_feature_callback(self):
        group = Group.objects.create(name="Group")
        source = GeoJSONSource.objects.create(
            name="test",
            geom_type=GeometryTypes.Point.value,
            file=os.path.join(os.path.dirname(__file__), "data", "test.geojson"),
            settings={"groups": [group.pk]},
        )
        layer = Layer.objects.create(name="test")
        feature = geostore_callbacks.feature_callback(
            source, layer, "id", GEOSGeometry("POINT (0 0)", srid=3857), {}
        )
        self.assertEqual(feature.geom.srid, 4326)

    def test_feature_callback_fail(self):
        def side_effect(msg):
            raise ValueError(msg)

        group = Group.objects.create(name="Group")
        source = GeoJSONSource.objects.create(
            name="test",
            geom_type=GeometryTypes.Point.value,
            file=os.path.join(os.path.dirname(__file__), "data", "test.geojson"),
            settings={"groups": [group.pk]},
        )
        layer = Layer.objects.create(name="test")
        with mock.patch(
            "django_geosource.geostore_callbacks.logger.warning",
            side_effect=side_effect,
        ):
            with self.assertRaisesRegexp(
                ValueError,
                "One record was ignored from source, because of "
                "invalid geometry: {'property': 'Hola'}",
            ):
                geostore_callbacks.feature_callback(
                    source, layer, "id", "Not a Point", {"property": "Hola"}
                )

    def test_clean_features(self):
        group = Group.objects.create(name="Group")
        source = GeoJSONSource.objects.create(
            name="test",
            geom_type=GeometryTypes.Point.value,
            file=os.path.join(os.path.dirname(__file__), "data", "test.geojson"),
            settings={"groups": [group.pk]},
        )
        layer = Layer.objects.create(name="test")
        Feature.objects.create(layer=layer, geom=GEOSGeometry("POINT (0 0)"))
        geostore_callbacks.clear_features(source, layer, layer.updated_at)

    def test_delete_layer(self):
        group = Group.objects.create(name="Group")
        source = GeoJSONSource.objects.create(
            name="test",
            geom_type=GeometryTypes.Point.value,
            file=os.path.join(os.path.dirname(__file__), "data", "test.geojson"),
            settings={"groups": [group.pk]},
        )
        layer = Layer.objects.create(name="test")
        Feature.objects.create(layer=layer, geom=GEOSGeometry("POINT (0 0)"))
        geostore_callbacks.delete_layer(source)
