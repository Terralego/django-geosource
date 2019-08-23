import unittest
from django_geosource_nodes import permissions
from unittest import mock
from django.contrib.auth.models import User
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from django.contrib.auth import authenticate
factory = APIRequestFactory()


class Test_TestPermissions(unittest.TestCase):
    def test_has_permissions(self):
        view = "view"
        sourcepermission = permissions.SourcePermission()
        request = Request(factory.get('/'))
        User.objects.create_user('ringo', 'starr@thebeatles.com', 'yellow')
        user = authenticate(username='ringo', password='yellow')
        request.user = user
        with mock.patch.object(request.user, 'has_perm') as mock_has_perm:
            mock_has_perm.return_value = True
            permission = sourcepermission.has_permission(request, view)
            self.assertTrue(permission)


if __name__ == '__main__':
    unittest.main()