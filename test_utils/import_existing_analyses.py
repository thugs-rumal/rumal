#!/usr/bin/env python
#
# import_existing_analyses.py
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA  02111-1307  USA
#
# Author:   Pietro Delsante <pietro.delsante@gmail.com>
#           The Honeynet Project
#

#!/usr/bin/env python

import django
import os
import pytz
import re
import sys
import time
from dateutil import parser
from pymongo import MongoClient

sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))
os.environ['DJANGO_SETTINGS_MODULE'] = 'rumal.settings'
django.setup()

from interface.models import *
from django.contrib.auth.models import User, Group

client      = MongoClient()
db          = client.thug
analyses    = db.analyses
urls        = db.urls

for analysis in analyses.find({'thug.version': re.compile(r'^0.6', re.I)}):
    if Task.objects.filter(object_id__exact=str(analysis['_id'])).count():
        print "Skipping analysis {} as it already exists".format(analysis['_id'])
        continue

    print "Adding analysis {} to Django's db".format(analysis['_id'])

    proxy = None
    if analysis['thug']['options']['proxy']:
        m = re.match('(?P<scheme>\w+)://(?:(?P<username>.+):(?P<password>.+)@)?(?P<host>[a-zA-Z0-9._-]+)(?::(?P<port>\d+))/?$', analysis['thug']['options']['proxy'], re.I)
        if m:
            proxy, created = Proxy.objects.get_or_create(
                scheme      = m.group('scheme'),
                username    = m.group('username'),
                password    = m.group('password'),
                host        = m.group('host'),
                port        = m.group('port'),
                default     = {
                    'user'  : User.objects.first()
                }
                )
            if created:
                print "Created new proxy: {}".format(proxy)
            else:
                print "Found existing proxy: {}".format(proxy)

    timestamp = parser.parse(analysis['timestamp']).replace(tzinfo=pytz.timezone(time.tzname[0]))

    t = Task(
        user            = User.objects.first(),
        submitted_on    = timestamp,
        started_on      = timestamp,
        completed_on    = timestamp,
        status          = STATUS_COMPLETED,
        object_id       = str(analysis['_id']),
        url             = urls.find_one({'_id': analysis['url_id']})['url'],
        referer         = analysis['thug']['options'].get('referer', None) == 'about:blank' and '' or analysis['thug']['options'].get('referer', None),
        useragent       = analysis['thug'].get('personality', {}).get('useragent', None),
        proxy           = proxy,
        events          = analysis['thug']['options'].get('events', None),
        delay           = analysis['thug']['options'].get('delay', None),
        timeout         = analysis['thug']['options'].get('timeout', None),
        threshold       = analysis['thug']['options'].get('threshold', None),
        no_cache        = analysis['thug']['options'].get('nocache', False),
        extensive       = analysis['thug']['options'].get('extensive', False),
        adobepdf        = analysis['thug']['plugins'].get('acropdf', None) == 'disabled' and None or analysis['thug']['plugins'].get('acropdf', None),
        no_adobepdf     = analysis['thug']['plugins'].get('acropdf', None) == 'disabled' and True or False,
        shockwave       = analysis['thug']['plugins'].get('shockwaveflash', None) == 'disabled' and None or analysis['thug']['plugins'].get('shockwaveflash', None),
        no_shockwave    = analysis['thug']['plugins'].get('shockwaveflash', None) == 'disabled' and True or False,
        javaplugin      = analysis['thug']['plugins'].get('javaplugin', None) == 'disabled' and None or analysis['thug']['plugins'].get('javaplugin', None),
        no_javaplugin   = analysis['thug']['plugins'].get('javaplugin', None) == 'disabled' and True or False,
    )
    t.save()
