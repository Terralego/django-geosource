from os.path import basename

from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from rest_framework.serializers import ModelSerializer, SerializerMethodField, ValidationError

from .models import GeoJSONSource, PostGISSource, Source, Field


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

    class Meta:
        fields = '__all__'
        read_only_fields = ('status', )
        model = Source

    @transaction.atomic
    def create(self, validated_data):
        # Fields can't be defined at source creation
        validated_data.pop('fields', None)
        source = super().create(validated_data)
        if source.run_sync_method('update_fields').result:
            return source
        raise ValidationError('Fields initialization failed')

    @transaction.atomic
    def update(self, instance, validated_data):
        fields = validated_data.pop('fields')
        source = super().update(instance, validated_data)

        for field_data in self.get_initial().get('fields', []):
            instance = source.fields.get(name=field_data.get('name'))

            serializer = FieldSerializer(instance=instance, data=field_data)
            if serializer.is_valid():
                serializer.save()
                if not source.run_sync_method('update_fields').result:
                    raise ValidationError('Fields update failed')

        return source


class PostGISSourceSerializer(SourceSerializer):

    class Meta:
        model = PostGISSource
        fields = '__all__'
        extra_kwargs = {
            'db_password': {'write_only': True}
        }


class GeoJSONSourceSerializer(SourceSerializer):
    filename = SerializerMethodField()

    def get_filename(self, instance):
        if instance.file:
            return basename(instance.file.path)

    class Meta:
        model = GeoJSONSource
        extra_kwargs = {
            'file': {'write_only': True}
        }
        fields = '__all__'
