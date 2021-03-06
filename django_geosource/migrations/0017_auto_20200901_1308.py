# Generated by Django 3.1 on 2020-09-01 13:08

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("django_geosource", "0016_auto_20200506_1444"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="field",
            options={"ordering": ("order",)},
        ),
        migrations.AddField(
            model_name="field",
            name="order",
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="postgissource",
            name="db_host",
            field=models.CharField(
                max_length=255,
                validators=[
                    django.core.validators.RegexValidator(
                        regex="(?:(?:25[0-5]|2[0-4]\\d|[0-1]?\\d?\\d)(?:\\.(?:25[0-5]|2[0-4]\\d|[0-1]?\\d?\\d)){3}|\\[[0-9a-f:.]+\\]|([a-z¡-\uffff0-9](?:[a-z¡-\uffff0-9-]{0,61}[a-z¡-\uffff0-9])?(?:\\.(?!-)[a-z¡-\uffff0-9-]{1,63}(?<!-))*\\.(?!-)(?:[a-z¡-\uffff-]{2,63}|xn--[a-z0-9]{1,59})(?<!-)\\.?|localhost))"
                    )
                ],
            ),
        ),
    ]
