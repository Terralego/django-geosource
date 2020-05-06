from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from django_geosource.serializers import CSVSourceSerializer


class CSVSourceSerializerTestCase(TestCase):
    def test_to_internal_value(self):
        csv = SimpleUploadedFile(name="test.csv", content=b"some content")
        data = {
            "file": [csv],
            "geom_type": 8,
            "_type": "CSVSource",
            "name": "test",
            "encoding": "UTF-8",
            "csr": "EPSG_4326",
            "coordinates_field": "two_columns",
            "latitude_field": "lat",
            "longitude_field": "long",
            "separator": "semicolon",
            "decimal_separator": "coma",
            "delimiter": "quotationmark",
            "number_lines_to_ignore": 0,
            "header": True,
        }
        serializer = CSVSourceSerializer(data=data)
        serializer.is_valid()
