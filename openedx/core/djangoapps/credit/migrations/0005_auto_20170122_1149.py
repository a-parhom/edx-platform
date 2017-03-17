# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('credit', '0004_auto_20170122_1141'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='creditrequirementstatus',
            options={'verbose_name_plural': 'Credit requirement statuses'},
        ),
        migrations.AlterField(
            model_name='creditconfig',
            name='cache_ttl',
            field=models.PositiveIntegerField(default=0, help_text='Specified in seconds. Enable caching by setting this to a value greater than 0.', verbose_name='Cache Time To Live'),
        ),
    ]
