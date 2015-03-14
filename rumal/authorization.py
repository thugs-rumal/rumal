#!/usr/bin/env python
#
# authorization.py
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

from django.db.models import Q
from tastypie.authorization import ReadOnlyAuthorization
from pymongo import Connection
from bson import ObjectId

from interface.models import *


db = Connection().thug

"""
Custom authorization classes.
For now, APIs are read-only. Every user should be allowed to see only their own objects
and the ones that are shared with them (e.g. with a group they're part of).
"""

class OwnAndSharedObjectsOnlyRelAuthorization(ReadOnlyAuthorization):
    # This class should only be used for objects coming from the relational database

    def read_list(self, object_list, bundle):
        # This assumes a ``QuerySet`` from ``ModelResource``.
        return object_list.filter(
                Q(user__exact = bundle.request.user) |
                Q(sharing_model__exact=SHARING_MODEL_PUBLIC) |
                (Q(sharing_model__exact=SHARING_MODEL_GROUPS) & Q(sharing_groups__in=bundle.request.user.groups.all()))
            )

    def read_detail(self, object_list, bundle):
        # Is the requested object public?
        if bundle.obj.sharing_model == SHARING_MODEL_PUBLIC:
            return True
        # Is the requested object owned by the user?
        if bundle.obj.user == bundle.request.user:
            return True
        # Is the requesting user in one of the sharing groups for the requested object?
        if bundle.obj.sharing_model == SHARING_MODEL_GROUPS:
            for group in bundle.obj.sharing_groups.all():
                if group in bundle.request.user.groups.all():
                    return True

        # Default action
        return False

class NonRelAuthorizationAbstract(ReadOnlyAuthorization):
    def _get_allowed_tasks(self, bundle):
        return Task.objects.filter(
                Q(user__exact = bundle.request.user) |
                Q(sharing_model__exact=SHARING_MODEL_PUBLIC) |
                (Q(sharing_model__exact=SHARING_MODEL_GROUPS) & Q(sharing_groups__in=bundle.request.user.groups.all()))
            ).values_list('object_id', flat=True)

    def _get_allowed_urls(self, bundle):
        # TODO: is there any more efficient way do accomplish this?
        allowed_urls = []
        for task in self._get_allowed_tasks(bundle):
            analysis = db.analyses.find_one({'_id': ObjectId(task)})
            if analysis:
                allowed_urls.append(str(analysis['url_id']))
            for connection in db.connections.find({'analysis_id': ObjectId(task)}):
                allowed_urls.append(str(connection['destination_id']))
        return allowed_urls

    def read_list(self, object_list, bundle):
        # This method is abstract
        raise NotImplementedError()

    def read_detail(self, object_list, bundle):
        # This method is abstract
        raise NotImplementedError()

class OwnAndSharedAnalysesOnlyNonRelAuthorization(NonRelAuthorizationAbstract):
    # This class should only be used for objects coming from the "analyses" collection of the non-relational database

    def read_list(self, object_list, bundle):
        # TODO: is there any more efficient way do accomplish this?
        allowed_tasks = self._get_allowed_tasks(bundle)
        allowed_list = []
        for obj in object_list:
            if '_id' in obj.keys() and str(obj['_id']) in allowed_tasks:
                allowed_list.append(obj)

        return allowed_list

    def read_detail(self, object_list, bundle):
        return Task.objects.filter(
                analysis_id__exact=bundle.obj['_id']
            ).filter(
                Q(user__exact = bundle.request.user) |
                Q(sharing_model__exact=SHARING_MODEL_PUBLIC) |
                (Q(sharing_model__exact=SHARING_MODEL_GROUPS) & Q(sharing_groups__in=bundle.request.user.groups.all()))
            ).count() > 0

class OwnAndSharedUrlsOnlyNonRelAuthorization(NonRelAuthorizationAbstract):
    # This class should only be used for objects coming from the "urls" collection of the non-relational database

    def read_list(self, object_list, bundle):
        allowed_urls = self._get_allowed_urls(bundle)

        allowed_list = []
        for obj in object_list:
            if '_id' in obj.keys() and str(obj['_id']) in allowed_urls:
                allowed_list.append(obj)

        return allowed_list

    def read_detail(self, object_list, bundle):
        return bundle.obj['_id'] in self._get_allowed_urls(bundle)

class OwnAndSharedObjectsOnlyNonRelAuthorization(NonRelAuthorizationAbstract):
    # This class should only be used for objects coming from the non-relational database that have a 'analysis_id' field

    def read_list(self, object_list, bundle):
        # TODO: is there any more efficient way do accomplish this?
        allowed_tasks = Task.objects.filter(
                Q(user__exact = bundle.request.user) |
                Q(sharing_model__exact=SHARING_MODEL_PUBLIC) |
                (Q(sharing_model__exact=SHARING_MODEL_GROUPS) & Q(sharing_groups__in=bundle.request.user.groups.all()))
            ).values_list('object_id', flat=True)

        allowed_list = []
        for obj in object_list:
            if 'analysis_id' in obj.keys() and str(obj['analysis_id']) in allowed_tasks:
                allowed_list.append(obj)

        return allowed_list

    def read_detail(self, object_list, bundle):
        return Task.objects.filter(
                analysis_id__exact=bundle.obj['analysis_id']
            ).filter(
                Q(user__exact = bundle.request.user) |
                Q(sharing_model__exact=SHARING_MODEL_PUBLIC) |
                (Q(sharing_model__exact=SHARING_MODEL_GROUPS) & Q(sharing_groups__in=bundle.request.user.groups.all()))
            ).count() > 0
