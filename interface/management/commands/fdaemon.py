#!/usr/bin/env python
#
# fdaemon.py
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

import ConfigParser
import logging
import os
import time
import requests
from posixpath import join as urljoin

from datetime import datetime
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from interface.models import *
from interface.api import TaskResource

import pymongo
import gridfs
from bson import ObjectId
from bson.json_util import loads,dumps

import json
from django.core import serializers
from interface.producer import Producer

import interface.utils

STATUS_NEW              = 0
STATUS_PROCESSING       = 1
STATUS_FAILED           = 2
STATUS_COMPLETED        = 3

NEW_SCAN_TASK = 1

RPC_QUEUE = 'rpc_queue'
RPC_PORT = 5672

config = ConfigParser.ConfigParser()
config.read(os.path.join(settings.BASE_DIR, "conf", "backend.conf"))
BACKEND_HOST = config.get('backend', 'host', 'http://localhost:8080')
API_KEY = config.get('backend', 'api_key', 'testkey')
API_USER = config.get('backend', 'api_user', 'testuser')

SLEEP_TIME_ERROR = 5
TASK_POST_URL = urljoin(BACKEND_HOST, "api/v1/task/")


# mongodb connection settings
client = pymongo.MongoClient()
db = client.thug
dbfs = client.thugfs
fs = gridfs.GridFS(dbfs)


logger = logging.getLogger(__name__)

class InvalidMongoIdException(Exception):
    pass

class Command(BaseCommand):

    active_scans = []

    def fetch_new_tasks(self):
        return Task.objects.filter(status__exact=STATUS_NEW).order_by('submitted_on')

    def fetch_pending_tasks(self):
        return Task.objects.filter(status__exact=STATUS_PROCESSING)
        # Task.objects.filter(status__exact=STATUS_PROCESSING).update(status=STATUS_NEW)

    def mark_as_running(self, task):
        logger.debug("[{}] Marking task as running".format(task.id))
        task.started_on = datetime.now(pytz.timezone(settings.TIME_ZONE))
        task.status = STATUS_PROCESSING
        task.save()

    def mark_as_failed(self, task):
        logger.debug("[{}] Marking task as failed".format(task.id))
        task.completed_on = datetime.now(pytz.timezone(settings.TIME_ZONE))
        task.status = STATUS_FAILED
        task.save()

    def mark_as_completed(self, task):
        logger.debug("[{}] Marking task as completed".format(task.id))
        task.completed_on = datetime.now(pytz.timezone(settings.TIME_ZONE))
        task.status = STATUS_COMPLETED
        task.save()

    def renderTaskDetail(self, pkval):
        return dumps(
            loads(
                serializers.serialize(
                    'json',
                    [Task.objects.get(pk=pkval), ]
                )
            )[0]
        )

    def post_new_task(self, task):
        temp1 = loads(self.renderTaskDetail(task.id))
        logger.info(BACKEND_HOST)

        temp = temp1['fields']
        temp.pop("user")
        temp.pop("sharing_model")
        temp.pop("plugin_status")
        temp.pop("sharing_groups")
        temp.pop("star")
        temp["frontend_id"] = temp1.pop("pk")
        temp["task"] = NEW_SCAN_TASK
        headers = {'Content-type': 'application/json', 'Authorization': 'ApiKey {}:{}'.format(API_USER,API_KEY)}
        logger.debug("Posting task {}".format(temp["frontend_id"]))

        scan = Producer(json.dumps(temp), 'localhost', RPC_PORT, RPC_QUEUE)
        self.active_scans.append(scan)
        self.mark_as_running(task)


    def search_samples_dict_list(self, search_id,sample_dict):
        "returns new gridfs sample_id"
        for x in sample_dict:
            if x["_id"] == search_id:
                return x["sample_id"]

    def retrieve_save_document(self, analysis_id):
        response = analysis_id
        #now files for locations
        for x in response["locations"]:
            if x['content_id'] != None:
                new_fs_id = get_file(x['content_id'])
                #now change id in repsonse
                x['location_id'] = new_fs_id
        # now for samples
        for x in response["samples"]:
            new_fs_id = get_file(x['sample_id'])
            #now change id in repsonse
            x['sample_id'] = new_fs_id
        # same for pcaps
        for x in response["pcaps"]:
            if x['content_id'] is None:
                continue
            new_fs_id = get_file(x['content_id'])
            #now change id in repsonse
            x['content_id'] = new_fs_id
        #for vt,andro etc. eoint sample_id to gridfs id
        # check for issues in this
        for x in response["virustotal"]:
            x['sample_id'] = search_samples_dict_list(x['sample_id'],response["samples"])
        for x in response["honeyagent"]:
            x['sample_id'] = search_samples_dict_list(x['sample_id'],response["samples"])
        for x in response["androguard"]:
            x['sample_id'] = search_samples_dict_list(x['sample_id'],response["samples"])
        for x in response["peepdf"]:
            x['sample_id'] = search_samples_dict_list(x['sample_id'],response["samples"])
        #remove id from all samples and pcaps
        for x in response["samples"]:
            x.pop("_id")
        response.pop("_id")
        frontend_analysis_id = db.analysiscombo.insert(response)
        return frontend_analysis_id

    def get_backend_status(self, pending_id_list):
    	if not pending_id_list:
    	    return [],[]
        semicolon_seperated = ";".join(pending_id_list)
        status_headers = {'Authorization': 'ApiKey {}:{}'.format(API_USER,API_KEY)}
        status_url = urljoin(BACKEND_HOST, "api/v1/status/set/{}/?format=json".format(semicolon_seperated))

        r = False
        while not r:
            try:
                r = requests.get(status_url, headers=status_headers)
            except requests.exceptions.ConnectionError:
                logger.debug("Got a requests.exceptions.ConnectionError exception, will try again in {} seconds".format(SLEEP_TIME_ERROR))
                time.sleep(SLEEP_TIME_ERROR)

        response = r.json()

        finished_on_backend = [x for x in response["objects"] if x["status"] == STATUS_COMPLETED]
        failed_on_backend = [x for x in response["objects"] if x["status"] == STATUS_FAILED]
        return finished_on_backend,failed_on_backend

    def process_response(self, response):
        task = Task.objects.get(id=response["frontend_id"])
        frontend_analysis_id = self.retrieve_save_document(response)
        task.object_id = frontend_analysis_id
        task.save()
        self.mark_as_completed(task)

    def decoder(self, dct):
        for k, v in dct.items():
            if '_id' in dct:
                try:
                    dct['_id'] = ObjectId(dct['_id'])
                except:
                    pass
            return dct

    def handle(self, *args, **options):
        logger.debug("Starting up frontend daemon")
        while True:
            logger.debug("Fetching new tasks to post to backend.")
            tasks = self.fetch_new_tasks()
            logger.debug("Got {} new tasks".format(len(tasks)))
            for task in tasks:
                self.post_new_task(task)

            logger.debug("Checking for complete tasks")
            for task in self.active_scans:
                if hasattr(task, 'response') and task.response is not None:
                    analysis = json.loads(task.response, object_hook=self.decoder)
                    if analysis["status"] is STATUS_COMPLETED:
                        logger.info("Task Completed")
                        response = analysis["data"]
                        self.process_response(response)
                        self.active_scans.remove(task)
                    else:
                        logger.info("Task Failed")
                        local_scan = Task.objects.get(id=analysis["data"])
                        self.mark_as_failed(local_scan)


            # logger.debug("Fetching pending tasks posted to backend.")
            # tasks = self.fetch_pending_tasks()
            # pending_id_list = [str(x.id) for x in tasks]
            # finished_on_backend,failed_on_backend = self.get_backend_status(pending_id_list)
            # for x in finished_on_backend:
            #     frontend_analysis_id = self.retrieve_save_document(x["object_id"])
            #     task = Task.objects.get(id=x["frontend_id"])
            #     task.object_id = frontend_analysis_id
            #     task.save()
            #     self.mark_as_completed(task)
            # for x in failed_on_backend:
            #     task = Task.objects.get(id=x["frontend_id"])
            #     self.mark_as_failed(task)
            logger.debug("Sleeping for {} seconds".format(6))
            time.sleep(6)

