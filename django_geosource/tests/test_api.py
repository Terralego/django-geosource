from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import GEOSGeometry
from django.test import TestCase
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED
from rest_framework.test import APIClient

from django_geosource.models import (
    PostGISSource,
    Source,
    Field,
    FieldTypes,
    GeometryTypes,
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
        "django_geosource.models.Source._get_records",
        MagicMock(return_value=[{"a": "b", "c": 42, "_geom_": "POINT(0 0)"}]),
    )
    def test_update_fields_method(self):
        obj = Source.objects.create(geom_type=10)
        obj.update_fields()

        self.assertEqual(FieldTypes.String.value, obj.fields.get(name="a").data_type)
        self.assertEqual(FieldTypes.Integer.value, obj.fields.get(name="c").data_type)
