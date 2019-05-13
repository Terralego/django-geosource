from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED
from rest_framework.test import APIClient

from django_geosource.models import PostGISSourceModel, SourceModel

UserModel = get_user_model()


class ModelSourceViewsetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.default_user = UserModel.objects.get_or_create(**{UserModel.USERNAME_FIELD:'testuser'})[0]
        self.client.force_authenticate(self.default_user)

    def test_list_view(self):
        # Create many sources and list them
        [PostGISSourceModel.objects.create() for x in range(5)]

        response = self.client.get(reverse('geosource:geosource-list'))
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(
            SourceModel.objects.count(),
            len(response.json()['results'])
        )

    def test_postgis_source_creation(self):
        source_example = {
            '_type': 'PostGISSourceModel',
            'db_username': 'username',
            'db_password': 'password',
            'db_name': 'dbname',
            'db_host': 'hostname.com',
        }

        response = self.client.post(
            reverse('geosource:geosource-list'),
            source_example,
            format='json'
        )
        self.assertEqual(response.status_code, HTTP_201_CREATED)
        self.assertDictEqual(response.json(), source_example)
