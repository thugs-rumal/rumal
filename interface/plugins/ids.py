#!/usr/bin/env python
#
# whoisplugin.py
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
#

import base64
import sys
import time
import os.path
import pymongo
import gridfs
import logging
import requests
try:
    import simplejson as json
except ImportError:
    import json

sys.path.append(os.path.abspath(os.path.join(
    os.path.dirname(__file__), os.path.pardir)))

from interface.plug import PluginBase

log = logging.getLogger(__name__)

TIMEOUT = 120
SLEEP_TIME = 10
MAX_ATTEMPTS = 120
STATUS_FAILED = -1      # Failed
STATUS_NEW = 0          # In queue
STATUS_PROCESSING = 1   # Processing
STATUS_QUEUED = 2       # Processing
STATUS_DONE = 3         # No further action required (completed or discarded)

# FIXME: read values from conf, or better give Plugin objects
# direct access to the database
client = pymongo.MongoClient()
db = client.thug
fs = gridfs.GridFS(db)


class IDSPlugin(PluginBase):
    @property
    def dependencies(self):
        """List of dependencies - put class names of required plugins here.
           Return blank list if none."""
        return []

    @property
    def module_dependencies(self):
        """List of non-standard lib module dependencies
           - put module names as keys and versions as
           values.Return blank list if none."""
        return
        {
            "requests": "2.6.0",
        }

    def submit(self, pcap):
        # FIXME: self.options
        api_url = self.options.get("api_url", None)
        api_key = self.options.get("api_key", None)
        username = self.options.get("username", None)

        log.debug("Will run with API user: {}, key: {}, URL: {}".format(
            username, api_key, api_url))

        if not api_url or not api_key or not username:
            raise RuntimeError("IDS module not properly configured, skip")

        self.headers = {
            'Authorization': 'ApiKey {}:{}'.format(username, api_key),
            'Content-Type': 'application/json'
        }

        with fs.get(pcap['_id']) as i:
            payload = {
                'pcap_file': {
                    "name": os.path.basename(self.pcap_path),
                    "file": base64.b64encode(i.read()),
                    "content_type": "application/vnd.tcpdump.pcap",
                }
            }

        response = None
        attempt = 0
        while response is None and attempt < MAX_ATTEMPTS:
            try:
                log.debug("Trying to POST pcap")
                response = requests.post(
                    os.path.join(api_url, 'task/'),
                    data=json.dumps(payload),
                    headers=self.headers
                )
            except requests.exceptions.ConnectionError:
                log.debug("Got requests.exceptions.ConnectionError, "
                          "trying again in one second")
                attempt += 1
                time.sleep(1)

        if not response:
            raise RuntimeError("Unable to contact the IDS APIs")

        if response.status_code == 201:
            retrieve_url = response.headers['Location']
            log.debug("Will need to poll URL: {}".format(retrieve_url))
        else:
            raise RuntimeError(
                "Unable to create new Extracted File, "
                "got status code: {}".format(response.status_code)
            )
        return retrieve_url

    def retrieve(self, retrieve_url):
        response = None
        try:
            log.debug("Trying to get results at {}".format(retrieve_url))
            response = requests.get(
                retrieve_url,
                headers=self.headers
            )
            if response.status_code != 200:
                log.debug("Got status code: {}".format(response.status_code))
                return None
            else:
                try:
                    ids = json.loads(response.text)
                except ValueError as e:
                    raise RuntimeError(
                        "Unable to convert response to "
                        "JSON: {0}".format(e)
                    )

                if ids['status'] == STATUS_DONE:
                    log.debug("Got response: {}".format(
                        json.dumps(ids['results'])))
                    return ids['results']
                elif ids['status'] == STATUS_FAILED:
                    raise RuntimeError("PCAP analysis failed")
                else:
                    log.debug("Got status: {}, try again later".format(
                        ids['status']))
                    return None

        except requests.exceptions.ConnectionError:
            log.debug("Got requests.exceptions.ConnectionError.")

    def run(self):
        """Run and make changes to data"""
        self.check_dependencies()
        pcap = self.data["pcaps"][0]
        retrieve_url = self.submit(pcap)

        elapsed = 0
        while elapsed <= TIMEOUT:
            sigs = self.retreive(retrieve_url)
            if sigs:
                self.data["pcaps"][0]["signatures"] = sigs
                break
            time.sleep(SLEEP_TIME)
            elapsed += SLEEP_TIME

        # 3. Call save data
        print "now trying to save_data", self.data
        self.save_data()
