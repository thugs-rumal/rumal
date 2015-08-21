# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('interface', '0002_auto_20150815_1308'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='star',
            field=models.ManyToManyField(default=None, related_name='star_tasks', null=True, to=settings.AUTH_USER_MODEL, blank=True),
            preserve_default=True,
        ),
    ]
