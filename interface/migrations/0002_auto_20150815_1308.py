# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import interface.models


class Migration(migrations.Migration):

    dependencies = [
        ('interface', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PluginTask',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('submitted_on', models.DateTimeField(default=interface.models.add_now, verbose_name=b'Submitted on', blank=True)),
                ('started_on', models.DateTimeField(default=None, null=True, verbose_name=b'Started on', blank=True)),
                ('completed_on', models.DateTimeField(default=None, null=True, verbose_name=b'Completed on', blank=True)),
                ('status', models.IntegerField(default=0, verbose_name=b'Status', blank=True)),
                ('plugin_name', models.CharField(max_length=100, verbose_name=b'Class Name of the Plugin')),
                ('task', models.ForeignKey(to='interface.Task')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='task',
            name='plugin_status',
            field=models.IntegerField(default=3, verbose_name=b'PluginStatus', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='task',
            name='no_javaplugin',
            field=models.BooleanField(default=False, verbose_name=b'Enable/ Disable Java plugin'),
            preserve_default=True,
        ),
    ]
