# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('interface', '0003_task_star'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='useragent',
            field=models.CharField(default=None, choices=[(b'', b'Default'), (b'nexuschrome18', 'Chrome 18.0.1025.133 (Google Nexus, Android 4.0.4)'), (b'galaxy2chrome18', 'Chrome 18.0.1025.166 (Samsung Galaxy S II, Android 4.0.3)'), (b'osx10chrome19', 'Chrome 19.0.1084.54 (MacOS X 10.7.4)'), (b'win7chrome20', 'Chrome 20.0.1132.47 (Windows 7)'), (b'winxpchrome20', 'Chrome 20.0.1132.47 (Windows XP)'), (b'galaxy2chrome25', 'Chrome 25.0.1364.123 (Samsung Galaxy S II, Android 4.0.3)'), (b'linuxchrome26', 'Chrome 26.0.1410.19 (Linux)'), (b'galaxy2chrome29', 'Chrome 29.0.1547.59 (Samsung Galaxy S II, Android 4.1.2)'), (b'linuxchrome30', 'Chrome 30.0.1599.15 (Linux)'), (b'ipadchrome33', 'Chrome 33.0.1750.21 (iPad, iOS 7.1)'), (b'ipadchrome35', 'Chrome 35.0.1916.41 (iPad, iOS 7.1.1)'), (b'ipadchrome37', 'Chrome 37.0.2062.52 (iPad, iOS 7.1.2)'), (b'ipadchrome38', 'Chrome 38.0.2125.59 (iPad, iOS 8.0.2)'), (b'ipadchrome39', 'Chrome 39.0.2171.45 (iPad, iOS 8.1.1)'), (b'win7chrome40', 'Chrome 40.0.2214.91 (Windows 7)'), (b'linuxchrome44', 'Chrome 44.0.2403.89 (Linux)'), (b'ipadchrome45', 'Chrome 45.0.2454.68 (iPad, iOS 8.4.1)'), (b'win7chrome45', 'Chrome 45.0.2454.85 (Windows 7)'), (b'ipadchrome46', 'Chrome 46.0.2490.73 (iPad, iOS 9.0.2)'), (b'winxpfirefox12', 'Firefox 12.0  (Windows XP)'), (b'linuxfirefox19', 'Firefox 19.0  (Linux)'), (b'win7firefox3', 'Firefox 3.6.13  (Windows 7)'), (b'linuxfirefox40', 'Firefox 40.0  (Linux)'), (b'win2kie60', 'Internet Explorer 6.0 (Windows 2000)'), (b'winxpie60', 'Internet Explorer 6.0 (Windows XP)'), (b'winxpie61', 'Internet Explorer 6.1 (Windows XP)'), (b'winxpie70', 'Internet Explorer 7.0 (Windows XP)'), (b'win2kie80', 'Internet Explorer 8.0 (Windows 2000)'), (b'win7ie80', 'Internet Explorer 8.0 (Windows 7)'), (b'winxpie80', 'Internet Explorer 8.0 (Windows XP)'), (b'win7ie90', 'Internet Explorer 9.0 (Windows 7)'), (b'osx10safari5', 'Safari 5.1.1  (MacOS X 10.7.2)'), (b'win7safari5', 'Safari 5.1.7  (Windows 7)'), (b'winxpsafari5', 'Safari 5.1.7  (Windows XP)'), (b'ipadsafari7', 'Safari 7.0  (iPad, iOS 7.0.4)'), (b'ipadsafari8', 'Safari 8.0  (iPad, iOS 8.0.2)'), (b'ipadsafari9', 'Safari 9.0  (iPad, iOS 9.1)')], max_length=50, blank=True, null=True, verbose_name=b'User Agent'),
            preserve_default=True,
        ),
    ]
