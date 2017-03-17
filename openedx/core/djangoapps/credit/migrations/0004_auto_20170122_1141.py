# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('credit', '0003_auto_20160511_2227'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='creditrequirementstatus',
            options={'verbose_name_plural': '\u0421\u0442\u0430\u0442\u0443\u0441 \u0437\u0430\u043f\u0438\u0442\u0443 \u043a\u0440\u0435\u0434\u0438\u0442\u0456\u0432'},
        ),
        migrations.AlterField(
            model_name='creditconfig',
            name='cache_ttl',
            field=models.PositiveIntegerField(default=0, help_text='\u0412\u0438\u0437\u043d\u0430\u0447\u0430\u0454\u0442\u044c\u0441\u044f \u0432 \u0441\u0435\u043a\u0443\u043d\u0434\u0430\u0445. \u0414\u043b\u044f \u0432\u043a\u043b\u044e\u0447\u0435\u043d\u043d\u044f \u043a\u0435\u0448\u0443\u0432\u0430\u043d\u043d\u044f \u0432\u043a\u0430\u0436\u0456\u0442\u044c \u0437\u043d\u0430\u0447\u0435\u043d\u043d\u044f \u0431\u0456\u043b\u044c\u0448\u0435 0.', verbose_name='\u041f\u0435\u0440\u0456\u043e\u0434 \u043e\u043d\u043e\u0432\u043b\u0435\u043d\u043d\u044f \u043a\u0435\u0448\u0443'),
        ),
    ]
