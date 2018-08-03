# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('student', '0008_certificateregenerationrequest'),
    ]

    operations = [
        migrations.AlterField(
            model_name='certificateregenerationrequest',
            name='status',
            field=models.CharField(max_length=255),
        ),
    ]
