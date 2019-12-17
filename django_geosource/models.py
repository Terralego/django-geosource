from datetime import datetime
from io import BytesIO
import logging
import json
from os import sys
from enum import Enum, IntEnum, auto

from celery.result import AsyncResult
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.postgres.fields import JSONField
from django.core.management import call_command
from django.core.validators import RegexValidator, URLValidator
from django.db import models, transaction
from django.utils.text import slugify
import fiona
from polymorphic.models import PolymorphicModel
import psycopg2
from psycopg2 import sql

from .callbacks import get_attr_from_path
from .celery import app as celery_app
from .fields import LongURLField
from .mixins import CeleryCallMethodsMixin
from .signals import refresh_data_done

logger = logging.getLogger(__name__)

# Decimal fields must be returned as float
DEC2FLOAT = psycopg2.extensions.new_type(
    psycopg2.extensions.DECIMAL.values,
    "DEC2FLOAT",
    lambda value, curs: float(value) if value is not None else None,
)
psycopg2.extensions.register_type(DEC2FLOAT)

HOST_REGEX = (
    rf"(?:{URLValidator.ipv4_re}|{URLValidator.ipv6_re}|{URLValidator.host_re})"
)


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

        return types.get(type(data), cls.Undefined)


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
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    id_field = models.CharField(max_length=255, default="id")
    geom_type = models.IntegerField(choices=GeometryTypes.choices())

    settings = JSONField(default=dict)

    task_id = models.CharField(null=True, max_length=255)
    task_date = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    SOURCE_GEOM_ATTRIBUTE = "_geom_"
    MAX_SAMPLE_DATA = 5

    class Meta:
        permissions = (("can_manage_sources", "Can manage sources"),)

    def get_layer(self):
        return get_attr_from_path(settings.GEOSOURCE_LAYER_CALLBACK)(self)

    def update_feature(self, *args):
        return get_attr_from_path(settings.GEOSOURCE_FEATURE_CALLBACK)(self, *args)

    def clear_features(self, layer, begin_date):
        return get_attr_from_path(settings.GEOSOURCE_CLEAN_FEATURE_CALLBACK)(
            self, layer, begin_date
        )

    def delete(self, *args, **kwargs):
        get_attr_from_path(settings.GEOSOURCE_DELETE_LAYER_CALLBACK)(self)
        return super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        return super().save(*args, **kwargs)

    def refresh_data(self):
        with transaction.atomic():
            layer = self.get_layer()
            begin_date = datetime.now()
            row_count = 0

            for row in self._get_records():
                geometry = row.pop(self.SOURCE_GEOM_ATTRIBUTE)
                try:
                    identifier = row[self.id_field]
                except KeyError:
                    raise Exception(
                        "Can't find identifier field in one or more records"
                    )
                self.update_feature(layer, identifier, geometry, row)
                row_count += 1

            self.clear_features(layer, begin_date)

        refresh_data_done.send_robust(
            sender=self.__class__, layer=layer.pk,
        )

        return {"count": row_count}

    @transaction.atomic
    def update_fields(self):
        records = self._get_records(50)

        fields = {}

        for record in records:
            record.pop(self.SOURCE_GEOM_ATTRIBUTE)

            for field_name, value in record.items():
                is_new = False

                if field_name not in fields:
                    field, is_new = self.fields.get_or_create(
                        name=field_name, defaults={"label": field_name}
                    )
                    field.sample = []
                    fields[field_name] = field

                if is_new or fields[field_name].data_type == FieldTypes.Undefined:
                    fields[field_name].data_type = FieldTypes.get_type_from_data(
                        value
                    ).value

                if (
                    len(fields[field_name].sample) < self.MAX_SAMPLE_DATA
                    and value is not None
                ):

                    if isinstance(value, bytes):
                        try:
                            value = value.decode()
                        except (UnicodeDecodeError, AttributeError):
                            logger.warning(
                                f"{field_name} couldn't be decoded for source {self.pk}"
                            )
                            continue

                    fields[field_name].sample.append(value)

        for field in fields.values():
            field.save()

        # Delete fields that are not anymore present
        self.fields.exclude(name__in=fields.keys()).delete()

        return {"count": len(fields)}

    def get_status(self):
        response = {}

        if self.task_id:
            task = AsyncResult(self.task_id, app=celery_app)
            response = {"state": task.state, "done": task.date_done}

            if task.successful():
                response["result"] = task.result
            if task.failed():
                task_data = task.backend.get(task.backend.get_key_for_task(task.id))
                response.update(json.loads(task_data).get("result", {}))

        return response

    def _get_records(self, limit=None):
        raise NotImplementedError

    def __str__(self):
        return f"{self.name} - {self.__class__.__name__}"

    @property
    def type(self):
        return self.__class__


class Field(models.Model):
    source = models.ForeignKey(Source, related_name="fields", on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=False)
    label = models.CharField(max_length=255)
    data_type = models.IntegerField(
        choices=FieldTypes.choices(), default=FieldTypes.Undefined.value
    )
    level = models.IntegerField(default=0)
    sample = JSONField(default=list)

    def __str__(self):
        return f"{self.name} ({self.source.name} - {self.data_type})"

    class Meta:
        unique_together = ["source", "name"]


class PostGISSource(Source):
    db_host = models.CharField(
        max_length=255, validators=[RegexValidator(regex=HOST_REGEX)],
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
        conn = psycopg2.connect(
            user=self.db_username,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            dbname=self.db_name,
        )
        return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def _get_records(self, limit=None):
        cursor = self._db_connection

        query = "SELECT * FROM ({}) q "
        attrs = [sql.SQL(self.query)]
        if limit:
            query += "LIMIT {}"
            attrs.append(sql.Literal(limit))

        cursor.execute(sql.SQL(query).format(*attrs))

        return cursor


class GeoJSONSource(Source):
    file = models.FileField(upload_to="geosource/geojson/%Y/")

    def get_file_as_dict(self):
        try:
            return json.load(self.file)
        except json.JSONDecodeError:
            logger.info("Source's GeoJSON file is not valid")
            raise

    def _get_records(self, limit=None):
        geojson = self.get_file_as_dict()

        limit = limit if limit else len(geojson["features"])

        records = []
        for record in geojson["features"][:limit]:
            try:
                records.append(
                    {
                        self.SOURCE_GEOM_ATTRIBUTE: GEOSGeometry(
                            json.dumps(record["geometry"])
                        ),
                        **record["properties"],
                    }
                )
            except ValueError:
                raise ValueError(
                    f"One of source's record has bad geometry: {record['geometry']}"
                )

        return records


class ShapefileSource(Source):
    file = models.FileField(upload_to="geosource/shapefile/%Y/")

    def _get_records(self, limit=None):
        with fiona.BytesCollection(self.file.read()) as shapefile:
            limit = limit if limit else len(shapefile)

            # Detect the EPSG
            _, srid = shapefile.crs.get("init", "epsg:4326").split(":")

            # Return geometries with a hack to set the correct geometry srid
            return [
                {
                    self.SOURCE_GEOM_ATTRIBUTE: GEOSGeometry(
                        GEOSGeometry(json.dumps(feature.get("geometry"))).wkt,
                        srid=int(srid),
                    ),
                    **feature.get("properties", {}),
                }
                for feature in shapefile[:limit]
            ]


class CommandSource(Source):
    command = models.CharField(max_length=255)

    @transaction.atomic
    def refresh_data(self):
        layer = self.get_layer()
        begin_date = datetime.now()

        sys.stdout.encoding = None
        sys.stdout.buffer = BytesIO()
        call_command(self.command)

        self.clear_features(layer, begin_date)

        refresh_data_done.send_robust(sender=self.__class__, layer=layer.pk)

        return {"count": None}

    def _get_records(self, limit=None):
        return []


class WMTSSource(Source):
    minzoom = models.IntegerField(null=True)
    maxzoom = models.IntegerField(null=True)
    tile_size = models.IntegerField()
    url = LongURLField()

    def get_status(self):
        return {"state": "DONT_NEED"}

    def refresh_data(self):
        return {}

    def _get_records(self, limit=None):
        return []
