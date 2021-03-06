# Generated by Django 3.1.1 on 2020-09-16 13:28

from django.db import migrations, models
import django_geosource.models


class Migration(migrations.Migration):

    dependencies = [
        ("django_geosource", "0017_auto_20200901_1308"),
    ]

    operations = [
        migrations.AlterField(
            model_name="field",
            name="data_type",
            field=models.IntegerField(
                choices=[
                    (1, django_geosource.models.FieldTypes["String"]),
                    (2, django_geosource.models.FieldTypes["Integer"]),
                    (3, django_geosource.models.FieldTypes["Float"]),
                    (4, django_geosource.models.FieldTypes["Boolean"]),
                    (5, django_geosource.models.FieldTypes["Undefined"]),
                    (6, django_geosource.models.FieldTypes["Date"]),
                ],
                default=5,
            ),
        ),
    ]
