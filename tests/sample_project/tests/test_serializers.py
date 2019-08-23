from django import forms
from django.test import TestCase
from django.core.validators import URLValidator
from django.db.models.fields import TextField
from django.forms.fields import URLField
from django.utils.translation import gettext_lazy as _
from django_geosource_nodes import serializers, models
from django.db import models
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.serializers import (IntegerField, ModelSerializer, SerializerMethodField, SlugField,
                                        ValidationError)
from django_geosource_nodes.celery import app as celery_app
from unittest import mock
from collections import OrderedDict


class Test_TestSerializers_PolymorphicModelSerializer(TestCase):
    def setUp(self):
        self.classe_source = serializers.Source.objects.create(
            name="name", slug="www.example.com/article/",
            description="description",
            id_field=1, geom_type=1, settings={}, status="status")
        self.classe_field = serializers.Field.objects.create(
            source=self.classe_source, name="name",
            label="label", level=5, sample={})
        
    # class Comment(models.Model):
    #     email = models.CharField(max_length=50)
    #     comment = models.CharField(max_length=50)

    # def test___new__(self):
        # test = {'many': True}
        # print(test.pop('many', False))
        # if test.pop('many', False): 
        #     print("marche")
        
        # {'Source': <class 'django_geosource_nodes.serializers.SourceSerializer'>,
        # 'PostGISSource': <class 'django_geosource_nodes.serializers.PostGISSourceSerializer'>,
        # 'GeoJSONSource': <class 'django_geosource_nodes.serializers.GeoJSONSourceSerializer'>,
        # 'ShapefileSource': <class 'django_geosource_nodes.serializers.ShapefileSourceSerializer'>,
        # 'CommandSource': <class 'django_geosource_nodes.serializers.CommandSourceSerializer'>, 
        # 'WMTSSource': <class 'django_geosource_nodes.serializers.WMTSSourceSerialize'>}     
        # classe = self.Comment.objects.create(email='foo@email.fr', content='whatever')
        # serializers.Source.objects.create(name="name", slug="www.example.com/article/", description="description"
        # ,  id_field=1, geom_type=1, settings={}, status="status")
        # classe = serializers.Field.objects.create( name="name",label="label",level=5,sample={}, source_id=1)
        # classe = serializers.Source.objects.create(name="name", slug="www.example.com/article/", description="description",
        #     id_field=1, geom_type=1, settings={}, status="status")
        # polymorphicmodelserializer = serializers.PolymorphicModelSerializer(
        #     classe, data={"_type": "Source"})
        # print(polymorphicmodelserializer)
        # self.assertTrue(polymorphicmodelserializer.is_valid())
        # print(polymorphicmodelserializer.is_valid())
        # print(polymorphicmodelserializer.validated_data)

    # def test__new__empty(self):
    #     with self.assertRaises(ValueError):
    #         serializers.PolymorphicModelSerializer()

    # def test_init__subclass(self):
    #     classe = serializers.FieldSerializer()
    #     print(classe.Meta)
    #     # polymorphicmodelserializer = serializers.PolymorphicModelSerializer()
    #     polymorphicmodelserializer = serializers.PolymorphicModelSerializer(classe, data={"_type": "Source"})
    #     polymorphicmodelserializer.is_valid()
    #     # polymorphicmodelserializer.save()
    #     # print(polymorphicmodelserializer.Meta)
    #     # subclass = polymorphicmodelserializer.__init_subclass__()
    
    def test_get_serializer_from_type_valid(self):
        data_type = "Source"
        polymorphicmodelserializer = serializers.PolymorphicModelSerializer()
        serializer = polymorphicmodelserializer.get_serializer_from_type(data_type)
        self.assertEqual(serializer, serializers.SourceSerializer)

    def test_get_serializer_from_type_exception(self):
        data_type = "KeyError"
        polymorphicmodelserializer = serializers.PolymorphicModelSerializer()
        with self.assertRaises(ValidationError):
            polymorphicmodelserializer.get_serializer_from_type(data_type)

    # @mock.patch('django_geosource_nodes.celery.app', mock.MagicMock(
    #     state="RUNNING", date_done=0, _get_task_meta_for=mock.MagicMock()))
    def test_to_representation(self):
        # print(self.classe_source.__class__.__name__)
        # result = task.delay()
        celery_app.backend.state = "RUNNING"
        celery_app.backend.date_done = 0 
        celery_app.backend._get_task_meta_for = mock.MagicMock()
        # print(celery_app.backend.state)
        # print(celery_app.backend.date_done)
        # test = celery_app.AsyncResult(1)
        # print(test.state)
        # print(celery_app)
        # res = celery_app.AsyncResult(1)
        # with mock.patch('celery.result.AsyncResult',
        #                        return_value=mock.Mock(ok=True))as mock_asyncresult:
        #     mock_asyncresult.return_value.state = 'RUNNING'
        #     mock_asyncresult.return_value.date_done = 0
        polymorphicmodelserializer = serializers.PolymorphicModelSerializer()
        representation = polymorphicmodelserializer.to_representation(
            self.classe_source)
        # print(representation)
        self.assertIsInstance(representation, dict)

    def test_to_internal_value(self):
        data = { 
            'label': 'here is the label',
            'level': 5,
        }
        fieldserializer = serializers.FieldSerializer(
            instance=self.classe_field, data=data)
        to_internal_value = fieldserializer.to_internal_value(data=data)
        self.assertTrue(fieldserializer.is_valid())
        self.assertIsInstance(to_internal_value, OrderedDict)
        self.assertEqual(dict(to_internal_value), data)

    def test_create(self):
        data = { 
            'label': 'here is the label',
            'level': 5,
            'source': self.classe_source,
        }
        fieldserializer = serializers.FieldSerializer(
            instance=self.classe_field, data=data)
        # fieldserializer.is_valid()
        # validated_data = fieldserializer.validated_data
        # print(validated_data)
        # validated_data_test = [('label', 'here is the label'), ('level', 5), ('source', self.classe_source)]
        validated_data_test = OrderedDict(data)
        # print(validated_data_test)
        create = fieldserializer.create(validated_data=validated_data_test)
        # print("create")
        # print(create)


# class Test_TestSerializers_SourceSerializer(TestCase):
    # def test_update_fields(self):
    #     source = serializers.Source.objects.create(
    #         name="name", slug="www.example.com/article/",
    #         description="description",
    #         id_field=1, geom_type=1, settings={}, status="status")
    #     source2 = serializers.Source.objects.create(
    #         name="name_2", slug="www.example.com/article/slug",
    #         description="description",
    #         id_field=2, geom_type=1, settings={}, status="status")
    #     # print(source.run_sync_method('update_fields', success_state='NEED_SYNC').result)
    #     sourceserializer = serializers.SourceSerializer(
    #         instance=source)
    #     sourceserializer._update_fields(source=source2)
    
    # def test_create(self):
    #     source = serializers.Source.objects.create(
    #         name="name", slug="www.example.com/article/",
    #         description="description",
    #         id_field=1, geom_type=1, settings={}, status="status")
    #     data = { 
    #         # 'label': 'here is the label',
    #         # 'level': 5,
    #         # 'source': source,
    #         '_type': 'Source',
    #         "geom_type": 1,
    #     }
    #     validated_data = OrderedDict(data)
    #     sourceserializer = serializers.SourceSerializer(
    #         instance=source)
    #     # sourceserializer.type_field = 'data_type'
    #     sourceserializer.create(validated_data)

    # def test_get_status(self):
    #     source = serializers.Source.objects.create(
    #         name="name", slug="www.example.com/article/",
    #         description="description",
    #         id_field=1, geom_type=1, settings={}, status="status")
        
    #     sourceserializer = serializers.SourceSerializer(
    #         instance=source)
    #     print(sourceserializer.get_status(source))

   