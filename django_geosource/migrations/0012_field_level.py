# Generated by Django 2.0.13 on 2019-07-05 12:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("django_geosource", "0011_auto_20190628_1449")]

    operations = [
        migrations.AddField(
            model_name="field", name="level", field=models.IntegerField(default=0)
        )
    ]
