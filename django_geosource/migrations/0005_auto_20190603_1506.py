# Generated by Django 2.0.13 on 2019-06-03 13:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_geosource', '0004_auto_20190529_1647'),
    ]

    operations = [
        migrations.AlterField(
            model_name='source',
            name='status',
            field=models.CharField(max_length=255, null=True),
        ),
    ]