from django.db import models
from django.core.validators import RegexValidator, URLValidator
from polymorphic.models import PolymorphicModel

class SourceModel(PolymorphicModel):
    @property
    def type(self):
        return self.__class__

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


class GeoJSONSourceModel(SourceModel):
    file = models.FileField(upload_to='geosource/')
