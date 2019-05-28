import logging
import json
from enum import Enum, IntEnum, auto
from django.conf import settings
from django.core.validators import RegexValidator, URLValidator
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.postgres.fields import JSONField
from django.db import models
from polymorphic.models import PolymorphicModel
import psycopg2
from psycopg2 import sql
from .callbacks import get_attr_from_path
from .mixins import CeleryCallMethodsMixin

logger = logging.getLogger(__name__)

# Decimal fields must be returned as float
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
    Undefined = auto()

    def _generate_next_value_(name, start, count, last_values):
        return name.lower()

    @classmethod
    def choices(cls):
        return [(enum.value, enum) for enum in cls]

    @classmethod
    def get_type_from_data(cls, data):
        types = {
            type(None): cls.Undefined,
            str: cls.String,
            int: cls.Integer,
            bool: cls.Boolean,
            float: cls.Float,
        }

        return types[type(data)]


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


class Source(PolymorphicModel, CeleryCallMethodsMixin):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    id_field = models.CharField(max_length=255, default='id')
    geom_type = models.IntegerField(choices=GeometryTypes.choices())

    status = models.NullBooleanField(default=None)

    SOURCE_GEOM_ATTRIBUTE = '_geom_'

    class Meta:
        permissions = (
            ('can_manage_sources', 'Can manage sources'),
        )

    def get_layer(self):
        return get_attr_from_path(settings.GEOSOURCE_LAYER_CALLBACK)(self)

    def update_feature(self, *args):
        return get_attr_from_path(settings.GEOSOURCE_FEATURE_CALLBACK)(self, *args)

    def refresh_data(self):
        try:
            layer = self.get_layer()

            for row in self._get_records():
                geometry = row.pop(self.SOURCE_GEOM_ATTRIBUTE)
                identifier = row.pop(self.id_field)
                try:

                    self.update_feature(layer, identifier, geometry, row)
                except Exception as e:
                    logger.error(f"An error occured during feature update: {e}")

            self.status = True
        except Exception as e:
            logger.error(f"An error occured during import : {e}")
            self.status = False
        finally:
            self.save()

    def update_fields(self):
        try:
            records = self._get_records(50)

            fields = {}

            for record in records:
                record.pop(self.SOURCE_GEOM_ATTRIBUTE)

                for field_name, value in record.items():
                    is_new = False

                    if field_name not in fields:
                        field, is_new = self.fields.get_or_create(name=field_name, defaults={'label': field_name, })
                        field.sample = []
                        fields[field_name] = field

                    fields[field_name].sample.append(value)

                    if is_new or fields[field_name].data_type == FieldTypes.Undefined:
                        fields[field_name].data_type = FieldTypes.get_type_from_data(value)


            for field in fields.values():
                field.save()

            # Delete fields that are not anymore present
            self.fields.exclude(name__in=fields.keys()).delete()

        except Exception as e:
            logger.error(f"An error occured during fields discovery : {e}")
            return False

        return True

    def _get_records(self, limit=None):
        raise NotImplementedError

    def __str__(self):
        return f'{self.name} - {self.__class__.__name__}'

    @property
    def type(self):
        return self.__class__


class Field(models.Model):
    source = models.ForeignKey(Source, related_name='fields', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=False)
    label = models.CharField(max_length=255)
    data_type = models.CharField(max_length=255, choices=FieldTypes.choices())
    sample = JSONField(default=[])

    def __str__(self):
        return f'{self.name} ({self.source.name} - {self.data_type})'

    class Meta:
        unique_together = ['source', 'name']


class PostGISSource(Source):
    db_host = models.CharField(
        max_length=255,
        validators=[
            RegexValidator(regex=r'(?:' + URLValidator.ipv4_re + '|' + URLValidator.ipv6_re + '|' + URLValidator.host_re + ')')
        ]
    )
    db_port = models.IntegerField(default=5432)
    db_username = models.CharField(max_length=63)
    db_password = models.CharField(max_length=255)
    db_name = models.CharField(max_length=63)

    query = models.TextField()

    geom_field = models.CharField(max_length=255)

    refresh = models.IntegerField(default=-1)

    @property
    def SOURCE_GEOM_ATTRIBUTE(self):
        return self.geom_field

    @property
    def _db_connection(self):
        conn = psycopg2.connect(user=self.db_username,
                                password=self.db_password,
                                host=self.db_host,
                                port=self.db_port,
                                dbname=self.db_name)
        return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def _get_records(self, limit=None):
        cursor = self._db_connection

        query = "SELECT * FROM ({}) q "
        attrs = [sql.SQL(self.query), ]
        if limit:
            query += "LIMIT {}"
            attrs.append(sql.Literal(limit))

        cursor.execute(
            sql.SQL(query).format(*attrs)
        )

        return cursor.fetchall()


class GeoJSONSource(Source):
    file = models.FileField(upload_to='geosource/')

    def get_file_as_dict(self):
        try:
            return json.load(self.file)
        except json.JSONDecodeError:
            logger.info("Source's GeoJSON file is not valid")
            raise

    def _get_records(self, limit=None):
        geojson = self.get_file_as_dict()

        limit = limit if limit else len(geojson['features'])

        return [
            {
                self.SOURCE_GEOM_ATTRIBUTE: GEOSGeometry(json.dumps(r['geometry'])),
                **r['properties']
            }
            for r in geojson['features'][:limit]
        ]
