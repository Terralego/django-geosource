import importlib
import unittest
import django
from django_geosource_nodes import callbacks


class Test_TestCallbacks(unittest.TestCase):
    def test_get_attr_from_path(self):
        result = callbacks.get_attr_from_path("math.floor")
        print(result)


if __name__ == '__main__':
    unittest.main()