# Generated by Django 2.0.13 on 2019-05-29 14:47

import django_geosource.models
from django.db import migrations, models
from django_geosource.models import FieldTypes


def fix_data_types(apps, schema_editor):
    Field = apps.get_model("django_geosource", "Field")
    for field in Field.objects.all():
        field.data_type = getattr(FieldTypes, "String").value
        field.save()


class Migration(migrations.Migration):

    dependencies = [("django_geosource", "0003_auto_20190528_1629")]

    operations = [
        migrations.RunPython(fix_data_types),
        migrations.AlterField(
            model_name="field",
            name="data_type",
            field=models.IntegerField(
                choices=[
                    (1, django_geosource.models.FieldTypes(1)),
                    (2, django_geosource.models.FieldTypes(2)),
                    (3, django_geosource.models.FieldTypes(3)),
                    (4, django_geosource.models.FieldTypes(4)),
                    (5, django_geosource.models.FieldTypes(5)),
                ],
                default=5,
            ),
        ),
    ]
