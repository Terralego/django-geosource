import json
from os.path import basename

from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from rest_framework.serializers import (IntegerField, ModelSerializer, SerializerMethodField, SlugField,
                                        ValidationError)

from .models import CommandSource, GeoJSONSource, PostGISSource, ShapefileSource, Source, Field, WMTSSource


class PolymorphicModelSerializer(ModelSerializer):

    type_field = '_type'
    type_class_map = {}

    def __new__(cls, *args, **kwargs):
        ''' Return the correct serializer depending of the type provided in the type_field
        '''

        if kwargs.pop('many', False):
            return cls.many_init(*args, **kwargs)


        if 'data' in kwargs:

            data_type = kwargs['data'].get(cls.type_field)

            serializer = cls.get_serializer_from_type(data_type)

            if serializer is not cls:
                return serializer(*args, **kwargs)

        return super().__new__(cls, *args, **kwargs)

    def __init_subclass__(cls, **kwargs):
        ''' Create a registry of all subclasses of the current class
        '''

        # Register all sub_classes
        cls.type_class_map[cls.Meta.model.__name__] = cls

    @classmethod
    def get_serializer_from_type(cls, data_type):
        if data_type in cls.type_class_map:
            return cls.type_class_map[data_type]
        raise ValidationError({cls.type_field: f"{data_type}'s type is unknown'"} )

    def to_representation(self, obj):
        serializer = self.get_serializer_from_type(obj.__class__.__name__)

        if serializer is self.__class__:
            data = {
                k: v
                for k, v in super().to_representation(obj).items()
                if k not in obj.polymorphic_internal_model_fields
            }
        else:
            data = serializer().to_representation(obj)

        data[self.type_field] = obj.__class__.__name__

        return data


    def to_internal_value(self, data):
        data_type = data.get(self.type_field)

        validated_data = super().to_internal_value(data)

        validated_data[self.type_field] = data_type

        return validated_data

    @transaction.atomic
    def create(self, validated_data):
        data_type = validated_data.pop(self.type_field, None)
        serializer = self.get_serializer_from_type(data_type)(validated_data)

        if serializer.__class__ is self.__class__:
            return super().create(validated_data)
        else:
            return serializer.create(validated_data)


class FieldSerializer(ModelSerializer):

    class Meta:
        model = Field
        exclude = ('source', )
        read_only_fields = ('name', 'sample', 'source', )


class SourceSerializer(PolymorphicModelSerializer):
    fields = FieldSerializer(many=True, required=False)
    status = SerializerMethodField()
    slug = SlugField(max_length=255, read_only=True)

    class Meta:
        fields = '__all__'
        model = Source

    def _update_fields(self, source):
        if source.run_sync_method('update_fields', success_state='NEED_SYNC').result:
            return source
        raise ValidationError('Fields update failed')

    @transaction.atomic
    def create(self, validated_data):
        # Fields can't be defined at source creation
        validated_data.pop('fields', None)
        source = super().create(validated_data)
        return self._update_fields(source)

    @transaction.atomic
    def update(self, instance, validated_data):
        validated_data.pop('fields')

        source = super().update(instance, validated_data)

        self._update_fields(source)

        for field_data in self.get_initial().get('fields', []):

            try:
                instance = source.fields.get(name=field_data.get('name'))

                serializer = FieldSerializer(instance=instance, data=field_data)

                if serializer.is_valid():
                    serializer.save()
                else:
                    raise ValidationError('Field configuration is not valid')
            except Field.DoesNotExist:
                pass

        return source

    def get_status(self, instance):
        return instance.get_status()


class PostGISSourceSerializer(SourceSerializer):

    class Meta:
        model = PostGISSource
        fields = '__all__'
        extra_kwargs = {
            'db_password': {'write_only': True}
        }


class GeoJSONSourceSerializer(SourceSerializer):
    filename = SerializerMethodField()

    def to_internal_value(self, data):
        if len(data.get('file', [])) > 0:
            data['file'] = data['file'][0]

        return super().to_internal_value(data)

    def get_filename(self, instance):
        if instance.file:
            return basename(instance.file.name)

    class Meta:
        model = GeoJSONSource
        fields = '__all__'
        extra_kwargs = {
            'file': {'write_only': True}
        }


class ShapefileSourceSerializer(SourceSerializer):
    filename = SerializerMethodField()

    def to_internal_value(self, data):
        if len(data.get('file', [])) > 0:
            data['file'] = data['file'][0]

        return super().to_internal_value(data)

    def get_filename(self, instance):
        if instance.file:
            return basename(instance.file.name)

    class Meta:
        model = ShapefileSource
        fields = '__all__'
        extra_kwargs = {
            'file': {'write_only': True}
        }


class CommandSourceSerializer(SourceSerializer):

    class Meta:
        model = CommandSource
        fields = '__all__'
        extra_kwargs = {
            'command': {
                'read_only': True,
                }
        }


class WMTSSourceSerialize(SourceSerializer):
    minzoom = IntegerField(min_value=0, max_value=24, allow_null=True)
    maxzoom = IntegerField(min_value=0, max_value=24, allow_null=True)

    class Meta:
        model = WMTSSource
        fields = '__all__'
