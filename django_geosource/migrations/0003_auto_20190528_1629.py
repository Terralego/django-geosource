# Generated by Django 2.0.13 on 2019-05-28 14:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("django_geosource", "0002_auto_20190524_1137")]

    operations = [
        migrations.AlterModelOptions(
            name="source",
            options={"permissions": (("can_manage_sources", "Can manage sources"),)},
        )
    ]
