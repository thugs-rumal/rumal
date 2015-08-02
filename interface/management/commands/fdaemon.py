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

import logging
import os
import time
import requests

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

STATUS_NEW              = 0
STATUS_PROCESSING       = 1
STATUS_FAILED           = 2
STATUS_COMPLETED        = 3

#Connection settings to be done manually
BACKEND_HOST = "" #add http://HOST
API_KEY = ""
API_USER = ""

TASK_POST_URL = BACKEND_HOST + "/api/v1/task/"


# mongodb connection settings
client = pymongo.MongoClient()
db = client.thug
dbfs = client.thugfs
fs = gridfs.GridFS(dbfs)


logger = logging.getLogger(__name__)

class InvalidMongoIdException(Exception):
    pass

class Command(BaseCommand):

    def fetch_new_tasks(self):
        return Task.objects.filter(status__exact=STATUS_NEW).order_by('submitted_on')

    def fetch_pending_tasks(self):
        return Task.objects.filter(status__exact=STATUS_PROCESSING)
        # Task.objects.filter(status__exact=STATUS_PROCESSING).update(status=STATUS_NEW)

    def mark_as_running(self, task):
        logger.info("[{}] Marking task as running".format(task.id))
        task.started_on = datetime.now(pytz.timezone(settings.TIME_ZONE))
        task.status = STATUS_PROCESSING
        task.save()

    def mark_as_failed(self, task):
        logger.info("[{}] Marking task as failed".format(task.id))
        task.completed_on = datetime.now(pytz.timezone(settings.TIME_ZONE))
        task.status = STATUS_FAILED
        task.save()

    def mark_as_completed(self, task):
        logger.info("[{}] Marking task as completed".format(task.id))
        task.completed_on = datetime.now(pytz.timezone(settings.TIME_ZONE))
        task.status = STATUS_COMPLETED
        task.save()

    def post_new_task(self,task):
        t = TaskResource()
        temp = loads(t.renderDetail(task.id))
        temp.pop("user")
        temp.pop("sharing_model")
        temp.pop("plugin_status")
        temp.pop("sharing_groups")
        temp["frontend_id"] = temp.pop("id")
        headers = {'Content-type': 'application/json', 'Authorization': 'ApiKey {}:{}'.format(API_USER,API_KEY)}
        logger.info("Posting task {}".format(temp["frontend_id"]))
        try:
            r = requests.post(TASK_POST_URL, json.dumps(temp), headers=headers)
        except requests.exceptions.ConnectionError:
            log.debug("Got a requests.exceptions.ConnectionError exception, will try again later.")
        if r.status_code == 201:
            self.mark_as_running(task)
        elif r.status_code == 401:
            log.debug("Got 401 - not authorized to acess resource.")

    def fetch_save_file(url):
        file_headers = {'Authorization': 'ApiKey {}:{}'.format(API_USER,API_KEY)}
        logger.info("Fetching file from {}".format(url))
        try:
            r = requests.get(url, headers = retrive_headers)
        except requests.exceptions.ConnectionError:
            log.debug("Got a requests.exceptions.ConnectionError exception, will try again later.")
            return None
        downloaded_file = r.content
        return str(fs.put(downloaded_file))

    def search_samples_dict_list(search_id,sample_dict):
        "returns new gridfs sample_id"
        for x in sample_dict:
            if x["_id"] == search_id:
                return x["sample_id"]

    def retrive_save_document(self,analysis_id):
        combo_resource_url = BACKEND_HOST + "/api/v1/analysiscombo/{}/?format=json".format(analysis_id)
        retrive_headers = {'Authorization': 'ApiKey {}:{}'.format(API_USER,API_KEY)}
        logger.info("Fetching resource from {}".format(combo_resource_url))
        try:
            r = requests.get(combo_resource_url, headers = retrive_headers)
        except requests.exceptions.ConnectionError:
            log.debug("Got a requests.exceptions.ConnectionError exception, will try again later.")
        response = loads(r.json())
        #now files for locations
        for x in response["locations"]:
            download_url = BACKEND_HOST + "/api/v1/location/" + x.sample_id + "/file/"
            new_fs_id = self.fetch_save_file(download_url)
            #now change id in repsonse
            x.location_id = new_fs_id
        # now for samples
        for x in response["samples"]:
            download_url = BACKEND_HOST + "/api/v1/sample/" + x.sample_id + "/file/"
            new_fs_id = self.fetch_save_file(download_url)
            #now change id in repsonse
            x.sample_id = new_fs_id
        #for vt,andro etc. point sample_id to gridfs id
        for x in response["virustotal"]:
            x.sample_id = search_samples_dict_list(x.sample_id,response["samples"])
        for x in response["honeyagent"]:
            x.sample_id = search_samples_dict_list(x.sample_id,response["samples"])
        for x in response["androguard"]:
            x.sample_id = search_samples_dict_list(x.sample_id,response["samples"])
        for x in response["peepdf"]:
            x.sample_id = search_samples_dict_list(x.sample_id,response["samples"])
        #remove id from all samples
        for x in response["samples"]:
            x.pop("_id")
        frontend_analysis_id = db.analysiscombo.insert(response)
        return frontend_analysis_id

    def get_backend_status(self,pending_id_list):
    	if not pending_id_list:
    	    return []
        semicolon_seperated = ";".join(pending_id_list) + ";"
        status_headers = {'Authorization': 'ApiKey {}:{}'.format(API_USER,API_KEY)}
        status_url = BACKEND_HOST + "/api/v1/status/set/{}/?format=json".format(semicolon_seperated)
        try:
            r = requests.get(status_url, headers=status_headers)
        except requests.exceptions.ConnectionError:
            log.debug("Got a requests.exceptions.ConnectionError exception, will try again later.")
        response = loads(r.json())
        finished_on_backend = [x for x in response["objects"] if x["status"] == 1]
        return finished_on_backend

    def handle(self, *args, **options):
        logger.info("Starting up frontend daemon")
        while True:
            logger.info("Fetching new tasks to post to backend.")
            tasks = self.fetch_new_tasks()
            logger.info("Got {} new tasks".format(len(tasks)))
            for task in tasks:
                # self._mark_as_running(task)
                self.post_new_task(task)
            logger.info("Fetching pending tasks posted to backend.")
            tasks = self.fetch_pending_tasks() if self.fetch_pending_tasks() else []
            pending_id_list = [str(x.id) for x in tasks]
            finished_on_backend = self.get_backend_status(pending_id_list)
            for x in finished_on_backend:
                frontend_analysis_id = retrive_save_document(x["object_id"])
                task = Task.objects.get(id=x["frontend_id"])
                task.analysis_id = frontend_analysis_id
                task.save()
                self.mark_as_completed(task)
            logger.info("Sleeping for {} seconds".format(60))
            time.sleep(60)

