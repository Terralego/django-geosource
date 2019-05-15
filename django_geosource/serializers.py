from django.core.exceptions import ImproperlyConfigured
from rest_framework.serializers import ModelSerializer, ValidationError

from .models import GeoJSONSourceModel, PostGISSourceModel, SourceModel, FieldModel


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

    def create(self, validated_data):
        data_type = validated_data.pop(self.type_field, None)
        serializer = self.get_serializer_from_type(data_type)(validated_data)

        if serializer.__class__ is self.__class__:
            return super().create(validated_data)
        else:
            return serializer.create(validated_data)

class FieldSerializer(ModelSerializer):

    class Meta:
        model = FieldModel
        exclude = ('source', )


class SourceModelSerializer(PolymorphicModelSerializer):
    fields = FieldSerializer(many=True)

    class Meta:
        fields = '__all__'
        model = SourceModel


class PostGISSourceModelSerializer(SourceModelSerializer):
    class Meta:
        model = PostGISSourceModel
        exclude = ('db_password', )


class GeoJSONSourceModelSerializer(SourceModelSerializer):
    class Meta:
        model = GeoJSONSourceModel
        fields = '__all__'
