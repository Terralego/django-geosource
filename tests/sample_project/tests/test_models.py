import unittest
import json
from rest_framework import parsers
from django_geosource_nodes import models
from enum import Enum
from django.utils.text import slugify


# class Test_TestModels_FieldTypes(unittest.TestCase):
    # def test_choices(self):
    #     Animal = Enum('Animal', 'ant bee cat dog')
    #     fieldtypes = models.FieldTypes('String')
        # fieldtypes._generate_next_value_(start=0, count=5, last_values=5)

class Test_TestModels_Source(unittest.TestCase):
    def setUp(self):
        self.source = models.Source.objects.create(
        name="name test", slug="www.example.com/article/",
        description="description",
        id_field=1, geom_type=1, settings={}, status="status")

    # def test_getlayer(self):
    #     print(self.source.get_layer())
    
    # def test_refresh_data(self):
    #     print(self.source.refresh_data())

    def test_save(self):
        self.source.save()
        self.assertEqual(self.source.slug, "name-test")


if __name__ == '__main__':
    unittest.main()