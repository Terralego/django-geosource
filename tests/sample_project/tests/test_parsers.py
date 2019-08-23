import unittest
import json
from rest_framework import parsers 
from django_geosource_nodes import parsers as parsers_geosource
from unittest import mock
import requests
from io import StringIO, BytesIO
from django.http import QueryDict
from django.test import client 
# from rest_framework.parsers import (
#     FileUploadParser, FormParser, JSONParser, MultiPartParser
# )
from django.core.files.uploadhandler import (
    MemoryFileUploadHandler, TemporaryFileUploadHandler
)


class Test_TestParsers_NestedMultipartJSONParser(unittest.TestCase):
    def test_nestedmultipartjsonparser_exception(self):
        class MockRequest:
            pass
        request = MockRequest()
        request.upload_handlers = (MemoryFileUploadHandler(),)
        stream = BytesIO(b'''{"creator":"creatorname","content":"postcontent","date":"04/21/2015"}''')
        nestedmultipartjsonparser = parsers_geosource.NestedMultipartJSONParser()
        request.META = {
            'HTTP_CONTENT_DISPOSITION': '''Content-Disposition: inline;
             filename=file.txt''',
            'HTTP_CONTENT_LENGTH': 14,
        }
        parser_context = {'request': request, 'kwargs': {}}
        stream.seek(0)
        with mock.patch.object(json, 'loads', 
                               side_effect=json.JSONDecodeError(
                    "test", "test2", 123)):
            result = nestedmultipartjsonparser.parse(
                stream=stream, media_type='''multipart/form-data;
                boundary=something''',
                parser_context=parser_context)
            # print(result.data)
            # print(result.files)


if __name__ == '__main__':
    unittest.main()




#     def test_nestedmultipartjsonparser_exception(self):
#         class MockRequest:
#             pass
#         request = MockRequest()
#         request.upload_handlers = (MemoryFileUploadHandler(),)
#         stream = BytesIO(bytes('''POST / HTTP/1.1
# [[ Less interesting headers ... ]]
# Content-Type: multipart/form-data; boundary=---------------------------735323031399963166993862150
# Content-Length: 14

# -----------------------------735323031399963166993862150
# Content-Disposition: form-data; name="text1"

# text default
# ''', 'utf8'))
#         nestedmultipartjsonparser = parsers.NestedMultipartJSONParser()
#         request.META = {
#             'HTTP_CONTENT_DISPOSITION': 'Content-Disposition: inline; filename=file.txt',
#             'HTTP_CONTENT_LENGTH': 14,
#         }
#         parser_context = {'request': request, 'kwargs': {}}
#         stream.seek(0)
#         result = nestedmultipartjsonparser.parse(
#             stream=stream, media_type='multipart/form-data; boundary=something',
#             parser_context=parser_context)
#         print(result.data)
#         print(result.files)
