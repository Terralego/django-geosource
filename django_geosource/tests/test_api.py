import logging
import os
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import GEOSGeometry
from django.test import TestCase
from django.urls import reverse
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_202_ACCEPTED,
    HTTP_400_BAD_REQUEST,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from rest_framework.test import APIClient

from django_geosource.models import (
    PostGISSource,
    Source,
    Field,
    FieldTypes,
    GeometryTypes,
    GeoJSONSource,
)

UserModel = get_user_model()


class ModelSourceViewsetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.default_user = UserModel.objects.get_or_create(
            is_superuser=True, **{UserModel.USERNAME_FIELD: "testuser"}
        )[0]
        self.client.force_authenticate(self.default_user)

    def test_list_view(self):
        # Create many sources and list them
        [
            PostGISSource.objects.create(
                name=f"test-{x}", refresh=-1, geom_type=GeometryTypes.LineString.value
            )
            for x in range(5)
        ]

        response = self.client.get(reverse("geosource:geosource-list"))
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(Source.objects.count(), len(response.json()))

    def test_refresh_view_fail(self):
        source = GeoJSONSource.objects.create(
            name="test",
            geom_type=GeometryTypes.Point.value,
            file=os.path.join(os.path.dirname(__file__), "data", "test.geojson"),
        )
        with patch(
            "django_geosource.mixins.CeleryCallMethodsMixin.run_async_method",
            return_value=False,
        ):
            response = self.client.get(
                reverse("geosource:geosource-refresh", args=[source.pk])
            )
        self.assertEqual(response.status_code, HTTP_500_INTERNAL_SERVER_ERROR)

    def test_refresh_view_accepted(self):
        source = GeoJSONSource.objects.create(
            name="test",
            geom_type=GeometryTypes.Point.value,
            file=os.path.join(os.path.dirname(__file__), "data", "test.geojson"),
        )
        with patch(
            "django_geosource.mixins.CeleryCallMethodsMixin.run_async_method",
            return_value=True,
        ):
            response = self.client.get(
                reverse("geosource:geosource-refresh", args=[source.pk])
            )
        self.assertEqual(response.status_code, HTTP_202_ACCEPTED)

    @patch(
        "django_geosource.serializers.PostGISSourceSerializer._first_record",
        MagicMock(return_value={"geom": GEOSGeometry("POINT (0 0)")}),
    )
    @patch(
        "django_geosource.models.Source.update_fields",
        MagicMock(return_value={"count": 1}),
    )
    @patch("django_geosource.models.Source.get_status", MagicMock(return_value={}))
    def test_postgis_source_creation(self):
        source_example = {
            "_type": "PostGISSource",
            "name": "Test Source",
            "db_username": "username",
            "db_name": "dbname",
            "db_host": "hostname.com",
            "query": "SELECT 1",
            "geom_field": "geom",
            "refresh": -1,
            "geom_type": GeometryTypes.LineString.value,
        }

        response = self.client.post(
            reverse("geosource:geosource-list"),
            {**source_example, "db_password": "test_password"},
            format="json",
        )

        self.assertEqual(response.status_code, HTTP_201_CREATED)
        self.assertDictContainsSubset(source_example, response.json())

    @patch(
        "django_geosource.serializers.PostGISSourceSerializer._first_record",
        MagicMock(return_value={"geom": GEOSGeometry("POINT (0 0)")}),
    )
    @patch(
        "django_geosource.models.Source.update_fields",
        MagicMock(return_value={"count": 1}),
    )
    @patch("django_geosource.models.Source.get_status", MagicMock(return_value={}))
    def test_postgis_source_creation_no_geom_field_wrong_geom(self):
        source_example = {
            "_type": "PostGISSource",
            "name": "Test Source",
            "db_username": "username",
            "db_name": "dbname",
            "db_host": "hostname.com",
            "query": "SELECT 1",
            "geom_field": None,
            "refresh": -1,
            "geom_type": GeometryTypes.LineString.value,
        }

        response = self.client.post(
            reverse("geosource:geosource-list"),
            {**source_example, "db_password": "test_password"},
            format="json",
        )
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertEqual(
            {"non_field_errors": ["No geom field found of type LineString"]},
            response.json(),
        )

    @patch(
        "django_geosource.serializers.PostGISSourceSerializer._first_record",
        MagicMock(return_value={"coucou": GEOSGeometry("LINESTRING (0 0, 1 1)")}),
    )
    @patch(
        "django_geosource.models.Source.update_fields",
        MagicMock(return_value={"count": 1}),
    )
    @patch("django_geosource.models.Source.get_status", MagicMock(return_value={}))
    def test_postgis_source_creation_no_geom_field_good_geom(self):
        source_example = {
            "_type": "PostGISSource",
            "name": "Test Source",
            "db_username": "username",
            "db_name": "dbname",
            "db_host": "hostname.com",
            "query": "SELECT 1",
            "geom_field": None,
            "refresh": -1,
            "geom_type": GeometryTypes.LineString.value,
        }

        response = self.client.post(
            reverse("geosource:geosource-list"),
            {**source_example, "db_password": "test_password"},
            format="json",
        )
        source_example["geom_field"] = "coucou"
        self.assertEqual(response.status_code, HTTP_201_CREATED)
        self.assertDictContainsSubset(source_example, response.json())

    @patch(
        "django_geosource.serializers.PostGISSourceSerializer._first_record",
        MagicMock(return_value={"geom": GEOSGeometry("POINT (0 0)")}),
    )
    @patch(
        "django_geosource.models.Source.update_fields",
        MagicMock(return_value={"count": 1}),
    )
    @patch("django_geosource.models.Source.get_status", MagicMock(return_value={}))
    def test_update_fields(self):
        source = PostGISSource.objects.create(
            name="Test Update Source",
            db_host="localhost",
            db_name="dbname",
            db_username="username",
            query="SELECT 1",
            geom_field="geom",
            refresh=-1,
            geom_type=GeometryTypes.LineString.value,
        )
        field = Field.objects.create(
            source=source,
            name="field_name",
            label="Label",
            data_type=FieldTypes.String.value,
        )

        response = self.client.get(
            reverse("geosource:geosource-detail", args=[source.pk])
        )
        self.assertEqual(response.status_code, HTTP_200_OK)

        test_field_label = "New Test Label"

        source_json = response.json()
        source_json["fields"][0]["label"] = test_field_label

        update_response = self.client.patch(
            reverse("geosource:geosource-detail", args=[source.pk]), source_json
        )

        self.assertEqual(update_response.status_code, HTTP_200_OK)
        self.assertEqual(
            update_response.json().get("fields")[0]["label"], test_field_label
        )

        field.refresh_from_db()
        self.assertEqual(field.label, test_field_label)

    @patch(
        "django_geosource.serializers.PostGISSourceSerializer._first_record",
        MagicMock(return_value={"geom": GEOSGeometry("POINT (0 0)")}),
    )
    @patch(
        "django_geosource.models.Source.update_fields",
        MagicMock(return_value={"count": 1}),
    )
    @patch("django_geosource.models.Source.get_status", MagicMock(return_value={}))
    def test_update_fields_fail_from_source(self):
        def run_sync_method_result(cmd, success_state):
            value = MagicMock()
            value.result = False
            return value

        source = PostGISSource.objects.create(
            name="Test Update Source",
            db_host="localhost",
            db_name="dbname",
            db_username="username",
            query="SELECT 1",
            geom_field="geom",
            refresh=-1,
            geom_type=GeometryTypes.LineString.value,
        )
        Field.objects.create(
            source=source,
            name="field_name",
            label="Label",
            data_type=FieldTypes.String.value,
        )
        response = self.client.get(
            reverse("geosource:geosource-detail", args=[source.pk])
        )
        self.assertEqual(response.status_code, HTTP_200_OK)

        test_field_label = "New Test Label"

        source_json = response.json()
        source_json["fields"][0]["label"] = test_field_label
        with patch(
            "django_geosource.mixins.CeleryCallMethodsMixin.run_sync_method",
            side_effect=run_sync_method_result,
        ):
            update_response = self.client.patch(
                reverse("geosource:geosource-detail", args=[source.pk]), source_json
            )
        self.assertEqual(update_response.status_code, HTTP_400_BAD_REQUEST)

    @patch(
        "django_geosource.models.Source._get_records",
        MagicMock(
            return_value=[{"a": "b", "c": 42, "d": b"4", "_geom_": "POINT(0 0)"}]
        ),
    )
    def test_update_fields_method(self):
        obj = Source.objects.create(geom_type=10)
        obj.update_fields()

        self.assertEqual(FieldTypes.String.value, obj.fields.get(name="a").data_type)
        self.assertEqual(FieldTypes.Integer.value, obj.fields.get(name="c").data_type)
        self.assertEqual(FieldTypes.Undefined.value, obj.fields.get(name="d").data_type)

    @patch(
        "django_geosource.models.Source._get_records",
        MagicMock(return_value=[{"a": "b", "c": 42, "_geom_": "POINT(0 0)"}]),
    )
    def test_update_fields_with_delete_method(self):
        obj = Source.objects.create(geom_type=10)
        Field.objects.create(
            source=obj,
            name="field_name",
            label="Label",
            data_type=FieldTypes.String.value,
        )
        obj.update_fields()

        self.assertEqual(FieldTypes.String.value, obj.fields.get(name="a").data_type)
        self.assertEqual(FieldTypes.Integer.value, obj.fields.get(name="c").data_type)
        self.assertEqual(0, Field.objects.filter(name="field_name").count())

    def test_ordering_filtering(self):
        obj = GeoJSONSource.objects.create(
            name="foo", geom_type=GeometryTypes.Point.value,
        )

        list_url = reverse("geosource:geosource-list")
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json()[0]["name"], obj.name)

        response = self.client.get(list_url, {"ordering": "-name"})
        self.assertEqual(response.json()[-1]["name"], obj.name)

        response = self.client.get(list_url, {"ordering": "polymorphic_ctype__model"})
        self.assertEqual(response.json()[0]["name"], obj.name)

        response = self.client.get(
            list_url, {"polymorphic_ctype__model": "geojsonsource"}
        )
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], obj.name)
