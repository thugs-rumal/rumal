#!/usr/bin/env python
#
# enrich.py
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
# Author:   Tarun Kumar <reach.tarun.here@gmail.com>
# NOTE: THIS IS AN INITIAL RELEASE AND IS LIKELY TO BE UNSTABLE

import logging
import os
import time
import requests

from datetime import datetime
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from interface.models import *
from interface.api import TaskResource
from interface.plug import PluginBase

import pymongo
import gridfs
from bson import ObjectId
from bson.json_util import loads, dumps

from interface.plugins import *

# mongodb connection settings
client = pymongo.MongoClient()
db = client.thug

# Now Importing All Plugins.
available_plugins = {}
for x in PluginBase.__subclasses__():
    available_plugins[x.__name__] = x

logger = logging.getLogger(__name__)


class InvalidMongoIdException(Exception):
    pass


# Add command to use available_plugins after selecting data.
