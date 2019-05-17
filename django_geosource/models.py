import logging
from enum import Enum, IntEnum, auto
from django.conf import settings
from django.core.validators import RegexValidator, URLValidator
from django.db import models
from django.contrib.postgres.fields import JSONField
from polymorphic.models import PolymorphicModel
import psycopg2
from .callbacks import get_attr_from_path
from .mixins import AsyncMethodsMixin

logger = logging.getLogger(__name__)


DEC2FLOAT = psycopg2.extensions.new_type(
    psycopg2.extensions.DECIMAL.values,
    'DEC2FLOAT',
    lambda value, curs: float(value) if value is not None else None)
psycopg2.extensions.register_type(DEC2FLOAT)


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


class SourceModel(PolymorphicModel, AsyncMethodsMixin):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    status = models.NullBooleanField(default=None)

    def get_layer(self):
        return get_attr_from_path(settings.GEOSOURCE_LAYER_CALLBACK)(self)

    def update_feature(self, layer, geometry, attributes):
        return get_attr_from_path(settings.GEOSOURCE_FEATURE_CALLBACK)(self, layer, geometry, attributes)

    def refresh_data(self):
        raise NotImplementedError

    def update_fields(self):
        raise NotImplementedError

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.run_async_method('update_fields')

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
    db_port = models.IntegerField()
    db_username = models.CharField(max_length=63)
    db_password = models.CharField(max_length=255)
    db_name = models.CharField(max_length=63)

    query = models.TextField()

    id_field = models.CharField(max_length=255, default='id')
    geom_field = models.CharField(max_length=255)
    geom_type = models.IntegerField(choices=GeometryTypes.choices())

    refresh = models.IntegerField()

    @property
    def _db_connection(self):
        conn = psycopg2.connect(user=self.db_username,
                                password=self.db_password,
                                host=self.db_host,
                                port=self.db_port,
                                dbname=self.db_name)
        return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def update_fields(self):
        pass

    def refresh_data(self):
        try:
            layer = self.get_layer()

            cursor = self._db_connection
            cursor.execute(self.query)
            logger.debug(self.query)
            for row in cursor.fetchall():
                geometry = row.pop(self.geom_field)

                try:
                    self.update_feature(layer, geometry, row)
                except Exception as e:
                    logger.error(f"An error occured during feature update: {e}")

            self.status = True
        except Exception as e:
            logger.error(f"An error occured during import : {e}")
            self.status = False
        finally:
            self.save()

class GeoJSONSourceModel(SourceModel):
    file = models.FileField(upload_to='geosource/')
