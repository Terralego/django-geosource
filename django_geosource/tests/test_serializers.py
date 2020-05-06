import os

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from django_geosource.models import CSVSource
from django_geosource.serializers import CSVSourceSerializer


class CSVSourceSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.settings_data = {
            "encoding": "UTF-8",
            "coordinate_reference_system": "EPSG_4326",
            "coordinates_field": "two_columns",
            "latitude_field": "lat",
            "longitude_field": "long",
            "field_separator": "semicolon",
            "decimal_separator": "coma",
            "char_delimiter": "doublequote",
            "number_lines_to_ignore": 0,
            "header": True,
        }

    def tearDown(self):
        for source in CSVSource.objects.all():
            os.remove(source.file.path)

    def test_to_internal_value_put_data_into_settings(self):
        csv = SimpleUploadedFile(name="test.csv", content=b"some content")
        data = {
            "file": [csv],
            "_type": "CSVSource",
            "name": "test",
            **self.settings_data,
        }
        serializer = CSVSourceSerializer(data=data)
        serializer.is_valid()
        serializer.save()

        self.assertTrue(CSVSource.objects.filter(settings=self.settings_data).exists())

    def test_data_representation_is_correct(self):
        csv = SimpleUploadedFile(name="test.csv", content=b"some content")
        data = {
            "file": csv,
            "geom_type": 0,
            "name": "test",
            "settings": self.settings_data,
        }
        csv_source = CSVSource.objects.create(**data)
        serializer = CSVSourceSerializer(csv_source)
        self.assertIsNone(serializer.data.get("settings"))

        # assert at least one of the settings element is at root level in serializer data
        # if it works for one, it works for all the other
        self.assertEqual(
            serializer.data.get("coordinate_reference_system"),
            csv_source.settings["coordinate_reference_system"],
        )
