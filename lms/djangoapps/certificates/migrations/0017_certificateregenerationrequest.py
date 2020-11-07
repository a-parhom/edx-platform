# -*- coding: utf-8 -*-

from django.conf import settings
from django.db import migrations, models
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CertificateRegenerationRequest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', CourseKeyField(max_length=255, db_index=True)),
                ('purpose', models.CharField(max_length=255)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('status', CourseKeyField(max_length=255)),
                ('modified', models.DateTimeField(default=django.utils.timezone.now)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]