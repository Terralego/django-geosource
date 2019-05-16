from enum import Enum, IntEnum, auto
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

    @classmethod
    def choices(cls):
        return [(enum.value, enum) for enum in cls]


class GeometryTypes(IntEnum):
    Point = 0
    LineString = 1
    # LinearRing 2
    Polygon = 3
    MultiPoint = 4
    MultiLineString = 5
    MultiPolygon = 6
    GeometryCollection = 7

    @classmethod
    def choices(cls):
        return [(enum.value, enum) for enum in cls]


class SourceModel(PolymorphicModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    status = models.NullBooleanField(default=None)

    @property
    def type(self):
        return self.__class__


class FieldModel(models.Model):
    source = models.ForeignKey(SourceModel, related_name='fields', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=False)
    label = models.CharField(max_length=255)
    data_type = models.CharField(max_length=255, choices=FieldTypes.choices())
    sample = JSONField(default=[])

    class Meta:
        unique_together = ['source', 'name']


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
    geom_type = models.IntegerField(choices=GeometryTypes.choices())

    refresh = models.IntegerField()


class GeoJSONSourceModel(SourceModel):
    file = models.FileField(upload_to='geosource/')
