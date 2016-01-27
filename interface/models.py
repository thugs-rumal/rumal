#!/usr/bin/env python
#
# models.py
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

import pytz
from datetime import datetime
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User, Group
from interface.utils import *

SHARING_MODEL_PUBLIC    = 0
SHARING_MODEL_PRIVATE   = 1
SHARING_MODEL_GROUPS    = 2
SHARING_MODEL_CHOICES = (
    (SHARING_MODEL_PUBLIC,      'Public'),
    (SHARING_MODEL_PRIVATE,     'Private'),
    (SHARING_MODEL_GROUPS,      'With Groups'),
)

STATUS_NEW              = 0
STATUS_PROCESSING       = 1
STATUS_FAILED           = 2
STATUS_COMPLETED        = 3
STATUS_CHOICES = (
    (STATUS_NEW,                'New'),
    (STATUS_PROCESSING,         'Processing'),
    (STATUS_FAILED,             'Failed'),
    (STATUS_COMPLETED,          'Completed'),
)

def add_now():
    return datetime.now(getattr(pytz, settings.TIME_ZONE))

class Proxy(models.Model):
    SCHEME_CHOICES = (
        ('http',    'http'),
        ('http2',   'http2'),
        ('socks4',  'socks4'),
        ('socks5',  'socks5'),
    )

    # User and sharing info
    user            = models.ForeignKey(User, null=True, blank=True, default=None)
    sharing_model   = models.IntegerField(null=False, blank=False, default=SHARING_MODEL_PUBLIC, choices=SHARING_MODEL_CHOICES)
    sharing_groups  = models.ManyToManyField(Group, blank=True, default=None)

    # Proxy info
    scheme          = models.CharField('Scheme', null=False, blank=False, max_length=10, choices=SCHEME_CHOICES)
    username        = models.CharField('Username', null=True, blank=True, max_length=50, default=None)
    password        = models.CharField('Password', null=True, blank=True, max_length=50, default=None)
    host            = models.CharField('Host', null=False, blank=False, max_length=50)
    port            = models.IntegerField('Port', null=False, blank=False)
    def __unicode__(self):
        return u'%s://%s:%s' % (self.scheme, self.host, self.port)

class Task(models.Model):
    # User and sharing info
    user            = models.ForeignKey(User, null=True, blank=True, default=None)
    sharing_model   = models.IntegerField(null=False, blank=False, default=SHARING_MODEL_PUBLIC, choices=SHARING_MODEL_CHOICES)
    sharing_groups  = models.ManyToManyField(Group, blank=True, default=None)
    star            = models.ManyToManyField(User, blank=True, default=None, related_name='star_tasks')
    # Metadata
    submitted_on    = models.DateTimeField("Submitted on", null=False, blank=True, default=add_now)
    started_on      = models.DateTimeField("Started on", null=True, blank=True, default=None)
    completed_on    = models.DateTimeField("Completed on", null=True, blank=True, default=None)
    status          = models.IntegerField("Status", null=False, blank=True, default=STATUS_NEW)
    plugin_status   = models.IntegerField("PluginStatus", null=False, blank=True, default=STATUS_COMPLETED)

    # ObjectID of Thug's analysis in MongoDB
    object_id       = models.CharField("ObjectID", null=True, blank=True, default=None, max_length=24)

    # Base options
    url             = models.CharField("Target URL", null=False, blank=False, max_length=4096)
    referer         = models.CharField("Referer", null=True, blank=True, default=None, max_length=4096)
    useragent       = models.CharField("User Agent", null=True, blank=True, default=None, max_length=50, choices=get_personalities())

    # Proxy
    proxy           = models.ForeignKey(Proxy, null=True, blank=True, default=None)

    # Other options
    events          = models.CharField("Specified DOM events handling", null=True, blank=True, default=None, max_length=4096)
    delay           = models.IntegerField("Maximum setTimeout/setInterval delay (milliseconds)", null=True, blank=True, default=None)
    timeout         = models.IntegerField("Analysis timeout (seconds)", null=True, blank=True, default=None)
    threshold       = models.IntegerField("Maximum pages to fetch", null=True, blank=True, default=None)
    no_cache        = models.BooleanField("Disable local web cache", null=False, blank=True, default=False)
    extensive       = models.BooleanField("Extensive fetch on linked pages", null=False, blank=True, default=False)
    broken_url      = models.BooleanField("Broken URL mode", null=False, blank=True, default=False)

    # Logging
    #logdir          = models.CharField("Log output directory", null=True, blank=True, default=None, max_length=4096)
    #output          = models.CharField("Log file", null=True, blank=True, default=None, max_length=4096)
    verbose         = models.BooleanField("Verbose mode", null=False, blank=True, default=False)
    quiet           = models.BooleanField("Quiet (disable console logging)", null=False, blank=True, default=False)
    debug           = models.BooleanField("Debug mode", null=False, blank=True, default=False)
    ast_debug       = models.BooleanField("AST debug mode (requires Debug mode)", null=False, blank=True, default=False)
    http_debug      = models.BooleanField("HTTP debug mode", null=False, blank=True, default=False)

    # External services
    vtquery         = models.BooleanField("Query VirusTotal for samples", null=False, blank=True, default=False)
    vtsubmit        = models.BooleanField("Submit samples to VirusTotal", null=False, blank=True, default=False)
    no_honeyagent   = models.BooleanField("Disable HoneyAgent support", null=False, blank=True, default=False)


    # Plugins
    adobepdf        = models.CharField("Adobe Acrobat Reader version (default: 9.1.0)", null=True, blank=True, default=None, max_length=30)
    no_adobepdf     = models.BooleanField("Disable Adobe Acrobat Reader plugin", null=False, blank=True, default=False)
    shockwave       = models.CharField("Shockwave Flash version (default: 10.0.64.0)", null=True, blank=True, default=None, max_length=30)
    no_shockwave    = models.BooleanField("Disable Shockwave Flash plugin", null=False, blank=True, default=False)
    javaplugin      = models.CharField("Java plugin version (default: 1.6.0.32)", null=True, blank=True, default=None, max_length=30)
    no_javaplugin   = models.BooleanField("Enable/ Disable Java plugin", null=False, blank=True, default=False)
    def __unicode__(self):
        return self.object_id

class PluginTask(models.Model):
    # Metadata
    submitted_on    = models.DateTimeField("Submitted on", null=False, blank=True, default=add_now)
    started_on      = models.DateTimeField("Started on", null=True, blank=True, default=None)
    completed_on    = models.DateTimeField("Completed on", null=True, blank=True, default=None)
    status          = models.IntegerField("Status", null=False, blank=True, default=STATUS_NEW)

    task = models.ForeignKey(Task)
    plugin_name = models.CharField("Class Name of the Plugin", max_length=100)

    def __unicode__(self):
        return str(self.plugin_name) + " " + str(self.status)

# Models for MongoDB objects
class Document(dict):
    # dictionary-like object for mongodb documents.
    __getattr__ = dict.get
