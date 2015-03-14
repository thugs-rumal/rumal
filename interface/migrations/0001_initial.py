# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import interface.models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Proxy',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sharing_model', models.IntegerField(default=0, choices=[(0, b'Public'), (1, b'Private'), (2, b'With Groups')])),
                ('scheme', models.CharField(max_length=10, verbose_name=b'Scheme', choices=[(b'http', b'http'), (b'http2', b'http2'), (b'socks4', b'socks4'), (b'socks5', b'socks5')])),
                ('username', models.CharField(default=None, max_length=50, null=True, verbose_name=b'Username', blank=True)),
                ('password', models.CharField(default=None, max_length=50, null=True, verbose_name=b'Password', blank=True)),
                ('host', models.CharField(max_length=50, verbose_name=b'Host')),
                ('port', models.IntegerField(verbose_name=b'Port')),
                ('sharing_groups', models.ManyToManyField(default=None, to='auth.Group', null=True, blank=True)),
                ('user', models.ForeignKey(default=None, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sharing_model', models.IntegerField(default=0, choices=[(0, b'Public'), (1, b'Private'), (2, b'With Groups')])),
                ('submitted_on', models.DateTimeField(default=interface.models.add_now, verbose_name=b'Submitted on', blank=True)),
                ('started_on', models.DateTimeField(default=None, null=True, verbose_name=b'Started on', blank=True)),
                ('completed_on', models.DateTimeField(default=None, null=True, verbose_name=b'Completed on', blank=True)),
                ('status', models.IntegerField(default=0, verbose_name=b'Status', blank=True)),
                ('object_id', models.CharField(default=None, max_length=24, null=True, verbose_name=b'ObjectID', blank=True)),
                ('url', models.CharField(max_length=4096, verbose_name=b'Target URL')),
                ('referer', models.CharField(default=None, max_length=4096, null=True, verbose_name=b'Referer', blank=True)),
                ('useragent', models.CharField(default=None, choices=[(b'', b'Default'), (b'nexuschrome18', b'Chrome 18.0.1025.133 (Google Nexus, Android 4.0.4)'), (b'galaxy2chrome18', b'Chrome 18.0.1025.166 (Samsung Galaxy S II, Android 4.0.3)'), (b'osx10chrome19', b'Chrome 19.0.1084.54 (MacOS X 10.7.4)'), (b'win7chrome20', b'Chrome 20.0.1132.47 (Windows 7)'), (b'winxpchrome20', b'Chrome 20.0.1132.47 (Windows XP)'), (b'galaxy2chrome25', b'Chrome 25.0.1364.123 (Samsung Galaxy S II, Android 4.0.3)'), (b'linuxchrome26', b'Chrome 26.0.1410.19 (Linux)'), (b'galaxy2chrome29', b'Chrome 29.0.1547.59 (Samsung Galaxy S II, Android 4.1.2)'), (b'linuxchrome30', b'Chrome 30.0.1599.15 (Linux)'), (b'ipadchrome33', b'Chrome 33.0.1750.21 (iPad, iOS 7.1)'), (b'ipadchrome35', b'Chrome 35.0.1916.41 (iPad, iOS 7.1.1)'), (b'ipadchrome37', b'Chrome 37.0.2062.52 (iPad, iOS 7.1.2)'), (b'ipadchrome38', b'Chrome 38.0.2125.59 (iPad, iOS 8.0.2)'), (b'ipadchrome39', b'Chrome 39.0.2171.45 (iPad, iOS 8.1.1)'), (b'win7chrome40', b'Chrome 40.0.2214.91 (Windows 7)'), (b'winxpfirefox12', b'Firefox 12.0  (Windows XP)'), (b'linuxfirefox19', b'Firefox 19.0  (Linux)'), (b'win7firefox3', b'Firefox 3.6.13  (Windows 7)'), (b'win2kie60', b'Internet Explorer 6.0 (Windows 2000)'), (b'winxpie60', b'Internet Explorer 6.0 (Windows XP)'), (b'winxpie61', b'Internet Explorer 6.1 (Windows XP)'), (b'winxpie70', b'Internet Explorer 7.0 (Windows XP)'), (b'win2kie80', b'Internet Explorer 8.0 (Windows 2000)'), (b'win7ie80', b'Internet Explorer 8.0 (Windows 7)'), (b'winxpie80', b'Internet Explorer 8.0 (Windows XP)'), (b'win7ie90', b'Internet Explorer 9.0 (Windows 7)'), (b'osx10safari5', b'Safari 5.1.1  (MacOS X 10.7.2)'), (b'win7safari5', b'Safari 5.1.7  (Windows 7)'), (b'winxpsafari5', b'Safari 5.1.7  (Windows XP)'), (b'ipadsafari7', b'Safari 7.0  (iPad, iOS 7.0.4)'), (b'ipadsafari8', b'Safari 8.0  (iPad, iOS 8.0.2)')], max_length=50, blank=True, null=True, verbose_name=b'User Agent')),
                ('events', models.CharField(default=None, max_length=4096, null=True, verbose_name=b'Specified DOM events handling', blank=True)),
                ('delay', models.IntegerField(default=None, null=True, verbose_name=b'Maximum setTimeout/setInterval delay (milliseconds)', blank=True)),
                ('timeout', models.IntegerField(default=None, null=True, verbose_name=b'Analysis timeout (seconds)', blank=True)),
                ('threshold', models.IntegerField(default=None, null=True, verbose_name=b'Maximum pages to fetch', blank=True)),
                ('no_cache', models.BooleanField(default=False, verbose_name=b'Disable local web cache')),
                ('extensive', models.BooleanField(default=False, verbose_name=b'Extensive fetch on linked pages')),
                ('broken_url', models.BooleanField(default=False, verbose_name=b'Broken URL mode')),
                ('verbose', models.BooleanField(default=False, verbose_name=b'Verbose mode')),
                ('quiet', models.BooleanField(default=False, verbose_name=b'Quiet (disable console logging)')),
                ('debug', models.BooleanField(default=False, verbose_name=b'Debug mode')),
                ('ast_debug', models.BooleanField(default=False, verbose_name=b'AST debug mode (requires Debug mode)')),
                ('http_debug', models.BooleanField(default=False, verbose_name=b'HTTP debug mode')),
                ('vtquery', models.BooleanField(default=False, verbose_name=b'Query VirusTotal for samples')),
                ('vtsubmit', models.BooleanField(default=False, verbose_name=b'Submit samples to VirusTotal')),
                ('no_honeyagent', models.BooleanField(default=False, verbose_name=b'Disable HoneyAgent support')),
                ('adobepdf', models.CharField(default=None, max_length=30, null=True, verbose_name=b'Adobe Acrobat Reader version (default: 9.1.0)', blank=True)),
                ('no_adobepdf', models.BooleanField(default=False, verbose_name=b'Disable Adobe Acrobat Reader plugin')),
                ('shockwave', models.CharField(default=None, max_length=30, null=True, verbose_name=b'Shockwave Flash version (default: 10.0.64.0)', blank=True)),
                ('no_shockwave', models.BooleanField(default=False, verbose_name=b'Disable Shockwave Flash plugin')),
                ('javaplugin', models.CharField(default=None, max_length=30, null=True, verbose_name=b'Java plugin version (default: 1.6.0.32)', blank=True)),
                ('no_javaplugin', models.BooleanField(default=False, verbose_name=b'Disable Java plugin')),
                ('proxy', models.ForeignKey(default=None, blank=True, to='interface.Proxy', null=True)),
                ('sharing_groups', models.ManyToManyField(default=None, to='auth.Group', null=True, blank=True)),
                ('user', models.ForeignKey(default=None, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
