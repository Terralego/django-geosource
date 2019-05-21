# Generated by Django 2.0.13 on 2019-05-21 09:09

from django.db import migrations, models
import django_geosource.models


class Migration(migrations.Migration):

    dependencies = [
        ('django_geosource', '0007_postgissourcemodel_id_field'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='postgissourcemodel',
            name='geom_type',
        ),
        migrations.AddField(
            model_name='sourcemodel',
            name='geom_type',
            field=models.IntegerField(choices=[(0, django_geosource.models.GeometryTypes(0)), (1, django_geosource.models.GeometryTypes(1)), (3, django_geosource.models.GeometryTypes(3)), (4, django_geosource.models.GeometryTypes(4)), (5, django_geosource.models.GeometryTypes(5)), (6, django_geosource.models.GeometryTypes(6)), (7, django_geosource.models.GeometryTypes(7))], default=7),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='fieldmodel',
            name='data_type',
            field=models.CharField(choices=[(1, django_geosource.models.FieldTypes(1)), (2, django_geosource.models.FieldTypes(2)), (3, django_geosource.models.FieldTypes(3)), (4, django_geosource.models.FieldTypes(4)), (5, django_geosource.models.FieldTypes(5))], max_length=255),
        ),
    ]
