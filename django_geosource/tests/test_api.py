from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model

UserModel = get_user_model()


class ModelSourceViewsetTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.default_user = UserModel.objects.get_or_create(**{UserModel.USERNAME_FIELD:'testuser'})[0]
        self.client.force_authenticate(self.default_user)

    def test_postgis_source_creation(self):
        response = self.client.post(
            reverse('geosource:geosource-list'),
            {
                '_type': 'PostGISSourceModel',
                'db_username': 'username',
                'db_password': 'password',
                'db_name': 'dbname',
                'db_host': 'hostname.com',
            },
            format='json'
        )
        print(response.json())

