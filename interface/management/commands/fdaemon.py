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

from django.core.management.base import BaseCommand, CommandError
from interface.models import *
from django.core import serializers

import pymongo
import gridfs
from bson import ObjectId
from bson.json_util import loads,dumps

import json
from bson import json_util
from interface.producer import Producer
import pika



STATUS_NEW              = 0  # identifies local status of task
STATUS_PROCESSING       = 1
STATUS_FAILED           = 2
STATUS_COMPLETED        = 3

NEW_SCAN_TASK = 1  # identifies data being sent to back end

SEND_ANY = 'Any'
ANY_QUEUE = 'any_queue'
PRIVATE_QUEUE = 'private_queue'
RPC_PORT = 5672

config = ConfigParser.ConfigParser()
config.read(os.path.join(settings.BASE_DIR, "conf", "backend.conf"))
BACKEND_HOST = config.get('backend', 'host', 'localhost')

# mongodb connection settings
client = pymongo.MongoClient()
db = client.thug
dbfs = client.thugfs
fs = gridfs.GridFS(dbfs)


logger = logging.getLogger(__name__)

class Command(BaseCommand):

    active_scans = []  # List of started threads waiting for a result to be returned from backend otr timeout

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
        temp = temp1['fields']
        backend = temp.pop("backend")
        temp.pop("user")
        temp.pop("sharing_model")
        temp.pop("plugin_status")
        temp.pop("sharing_groups")
        temp.pop("star")
        temp["frontend_id"] = temp1.pop("pk")
        temp["task"] = NEW_SCAN_TASK
        logger.debug("Posting task {}".format(temp["frontend_id"]))
        if backend == SEND_ANY:
            #  start the thread to post the scan on any queue
            scan = Producer(json.dumps(temp), BACKEND_HOST, RPC_PORT, ANY_QUEUE, temp["frontend_id"])
            scan.start()
            self.active_scans.append(scan)
            self.mark_as_running(task)
        else:
            #  start the thread to post the scan on private queue
            scan = Producer(json.dumps(temp), backend, RPC_PORT, PRIVATE_QUEUE, temp["frontend_id"])
            scan.start()
            self.active_scans.append(scan)
            self.mark_as_running(task)

    def search_samples_dict_list(self, search_id,sample_dict):
        "returns new gridfs sample_id"
        for x in sample_dict:
            if x["_id"] == search_id:
                return x["sample_id"]

    def retrieve_save_document(self, response, files):
        #  now files for locations
        for x in response["locations"]:
            if x['content_id'] is not None:
                dfile = [item["data"] for item in files if str(item["content_id"]) == x["content_id"]][0]
                new_fs_id = str(fs.put(dfile.encode('utf-8')))
                #  now change id in repsonse
                x['location_id'] = new_fs_id
        # now for samples
        for x in response["samples"]:
            dfile = [item["data"] for item in files if str(item["sample_id"]) == x["sample_id"]][0]
            new_fs_id = str(fs.put(dfile.encode('utf-8')))
            #n  ow change id in repsonse
            x['sample_id'] = new_fs_id
        # same for pcaps
        for x in response["pcaps"]:
            if x['content_id'] != None:
                dfile = [item["data"] for item in files if str(item["content_id"]) == x["content_id"]][0]
                new_fs_id = str(fs.put(dfile.encode('utf-8')))
            #  now change id in repsonse
            x['content_id'] = new_fs_id
        #  for vt,andro etc. eoint sample_id to gridfs id
        #  check for issues in this
        for x in response["virustotal"]:
            x['sample_id'] = self.search_samples_dict_list(x['sample_id'],response["samples"])
        for x in response["honeyagent"]:
            x['sample_id'] = self.search_samples_dict_list(x['sample_id'],response["samples"])
        for x in response["androguard"]:
            x['sample_id'] = self.search_samples_dict_list(x['sample_id'],response["samples"])
        for x in response["peepdf"]:
            x['sample_id'] = self.search_samples_dict_list(x['sample_id'],response["samples"])
        #  remove id from all samples and pcaps
        for x in response["samples"]:
            x.pop("_id")
        response.pop("_id")
        frontend_analysis_id = db.analysiscombo.insert(response)
        return frontend_analysis_id

    def process_response(self, task):

        analysis = json.loads(task.response, object_hook=decoder)
        if analysis["status"] is STATUS_COMPLETED:
            logger.info("Task Completed")

            analysis_response = analysis["data"]
            files = json_util.loads(analysis["files"])
            local_task = Task.objects.get(id=analysis_response["frontend_id"])

            frontend_analysis_id = self.retrieve_save_document(analysis_response, files)

            local_task.object_id = frontend_analysis_id
            local_task.save()

            self.mark_as_completed(local_task)
            self.active_scans.remove(task)
        else:
            logger.info("Task Failed")
            local_scan = Task.objects.get(id=analysis["data"])
            self.mark_as_failed(local_scan)
            self.active_scans.remove(task)

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
                if task.thread_exception is None:
                    if hasattr(task, 'response') and task.response is not None:
                        self.process_response(task)
                else:
                    if task.thread_exception == pika.exceptions.ConnectionClosed:
                        logger.info("Cannot make connection to backend via {} {} {}".format(task.host,
                                                                                            task.port,
                                                                                            task.routing_key))
                    if task.thread_exception == TimeOutException:
                        logger.info("Task {} took too long to reply".format(int(task.frontend_id)))
                    if task.thread_exception == pika.exceptions.ProbableAuthenticationError or \
                                    task.thread_exception == pika.exceptions.ProbableAccessDeniedError:
                        logger.info("Task {} Authentication Error".format(int(task.frontend_id)))
                    self.mark_as_failed(Task.objects.filter(pk=int(task.frontend_id))[0])
                    self.active_scans.remove(task)

            logger.debug("Sleeping for {} seconds".format(6))
            time.sleep(6)

