from enum import Enum, auto
from django.core.validators import RegexValidator, URLValidator
from django.db import models
from django.contrib.postgres.fields import JSONField
from polymorphic.models import PolymorphicModel

class FieldTypes(Enum):
    String = auto()
    Integer = auto()
    Float = auto()
    Boolean = auto()

    def _generate_next_value_(name, start, count, last_values):
        return name.lower()


class SourceModel(PolymorphicModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    status = models.NullBooleanField(default=None)

    @property
    def type(self):
        return self.__class__


class FieldModel(models.Model):
    source = models.ForeignKey(SourceModel, related_name='fields', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    label = models.CharField(max_length=255)
    data_type = models.CharField(max_length=255, choices=[(tag, tag.value) for tag in FieldTypes])
    sample = JSONField(default=[])


class PostGISSourceModel(SourceModel):
    db_host = models.CharField(
        max_length=255,
        validators=[
            RegexValidator(regex=r'(?:' + URLValidator.ipv4_re + '|' + URLValidator.ipv6_re + '|' + URLValidator.host_re + ')')
        ]
    )
    db_username = models.CharField(max_length=63)
    db_password = models.CharField(max_length=255)
    db_name = models.CharField(max_length=63)

    query = models.TextField()
    geom_field = models.CharField(max_length=255)

    refresh = models.IntegerField()


class GeoJSONSourceModel(SourceModel):
    file = models.FileField(upload_to='geosource/')
