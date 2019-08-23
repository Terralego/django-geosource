from django import forms
import unittest
from django.core.validators import URLValidator
from django.db.models.fields import TextField
from django.forms.fields import URLField
from django.utils.translation import gettext_lazy as _
from django_geosource_nodes import fields



class Test_TestFields_LongURLField(unittest.TestCase):
    def test_formfield(self):
        longurlfield = fields.LongURLField("https://example_https")
        result = longurlfield.formfield()
        # print(result.max_length)
        # print(type(result))
        self.assertIsInstance(result, URLField)


if __name__ == '__main__':
    unittest.main()