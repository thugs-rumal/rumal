#!/usr/bin/env python
#
# api.py
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
# Author:   Pietro Delsante <pietro.delsante AT gmail.com>
#           The Honeynet Project
#

from json import dumps, loads
from tastypie import fields
from tastypie.resources import ModelResource, ALL_WITH_RELATIONS, ALL, Resource
from tastypie.authentication import SessionAuthentication, ApiKeyAuthentication, MultiAuthentication
from tastypie.authorization import DjangoAuthorization, ReadOnlyAuthorization
from django.contrib.auth.models import User, Group
from django.core import serializers
from rumal.authorization import *
from django.shortcuts import get_object_or_404

from interface.models import *
from interface.resources import MongoDBResource
from interface.highlights import generate_warnings, generate_threats
from interface.utils import make_nested_tree
import advanced_search
import pymongo

from django.http import HttpRequest

"""
Resources for SQLite models
"""

class GroupResource(ModelResource):
    class Meta:
        queryset = Group.objects.all()
        resource_name = 'group'
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        authorization = DjangoAuthorization()
        always_return_data = True
        filtering = {
            'id': ALL,
            'name': ALL,
        }

class CurrentUserResource(ModelResource):

    groups = fields.ToManyField(GroupResource, 'groups',
                                blank=True)

    class Meta:
        queryset        = User.objects.all()
        resource_name   = 'current-user'

        allowed_methods = ['get']
        fields          = ['id', 'username']
        ordering        = ['id', 'username']
        filtering = {
          'username': ALL_WITH_RELATIONS,
          'groups': ALL_WITH_RELATIONS
        }

    def get_object_list(self, request):
        users = super(CurrentUserResource, self).get_object_list(request)
        return users.filter(id=request.user.id)

class UserResource(ModelResource):
    class Meta:
        queryset        = User.objects.all()
        resource_name   = 'user'
        authentication  = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        authorization   = DjangoAuthorization()
        allowed_methods = ['get']
        fields          = ['id', 'username']
        ordering        = ['id', 'username']
        filtering = {
          'username': ALL,
        }

class ProxyResource(ModelResource):
    class Meta:
        queryset        = Proxy.objects.all()
        resource_name   = 'proxy'
        authentication  = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        authorization   = OwnAndSharedObjectsOnlyRelAuthorization()
        allowed_methods = ['get']
        include_resource_uri = False
        excludes = ["id",]


class TaskResource(ModelResource):
    proxy           = fields.ForeignKey(ProxyResource, 'proxy', full=True, null=True)
    user            = fields.ForeignKey(UserResource, 'user', full=True)
    sharing_groups  = fields.ToManyField(GroupResource, 'sharing_groups', full=True, null=True)
    star            = fields.ToManyField(UserResource, 'star', full=True, null=True)

    def renderDetail(self,pkval):
        return dumps(
            loads(
                serializers.serialize(
                    'json',
                    [Task.objects.get(pk=pkval),]
                )
            )[0]
        )

    def apply_filters(self, request, applicable_filters):
        """
        accept extra query in request
        """
        my_scan = request.GET.get('myscans', None)
        starred = request.GET.get('starred', None)

        semi_filtered = super(TaskResource, self).apply_filters(request, applicable_filters)

        if my_scan:
            filtered_objects = semi_filtered.filter(user__username__exact=request.user.username)
            return filtered_objects.distinct()

        elif starred:
            filtered_objects = semi_filtered.filter(star=request.user)
            return filtered_objects.distinct()

        else:
            return semi_filtered.distinct()


    class Meta:
        queryset        = Task.objects.all()
        resource_name   = 'task'
        authentication  = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        authorization   = OwnAndSharedObjectsOnlyRelAuthorization()
        allowed_methods = ['get']
        include_resource_uri = False
        limit = 0
        ordering        = [
            'id',
            'user__username',
            'sharing_model',
            'sharing_groups__name',
            'submitted_on',
            'started_on',
            'completed_on',
            'status',
            'url',
            'referer',
            'useragent',
            'proxy',
        ]
        filtering = {
          'user': ALL_WITH_RELATIONS,
          'star': ALL_WITH_RELATIONS,
          'id': ALL_WITH_RELATIONS
        }

class CommentResource(ModelResource):
    task = fields.ForeignKey(TaskResource, 'task', full=True)
    user = fields.ForeignKey(UserResource, 'user', full=True)

    def apply_filters(self, request, applicable_filters):
        task_id = request.GET.get('task_id', None)
        node = request.GET.get('node', None)

        task = get_object_or_404(Task, pk=task_id)

        semi_filtered = super(CommentResource, self).apply_filters(request, applicable_filters)
        if task_id and node:
            if task.sharing_model is SHARING_MODEL_PUBLIC or request.user == task.user or check_group(request, task):
                filtered_objects = semi_filtered.filter(task__id=task_id).filter(node=node)
                return filtered_objects
        return None


    class Meta:
        queryset = Comment.objects.all()
        resource_name = 'comments'
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        authorization = DjangoAuthorization()
        allowed_methods = ['get']
        limit = 0
        filtering = {
            'task': ALL_WITH_RELATIONS,
            'node': ALL_WITH_RELATIONS

        }


"""Non ORM Model for advanced search"""

class Object(object):
    """
    Container to keep data that doesn't conform to any orm model, but has to be returned
    by some resources.
    """

    def __init__(self, initial=None):
        self.__dict__['_data'] = {}

        if hasattr(initial, 'items'):
            self.__dict__['_data'] = initial

    def __getattr__(self, name):
        return self._data.get(name, None)

    def __setattr__(self, name, value):
        self.__dict__['_data'][name] = value

    def to_dict(self):
        return self._data



class AdvancedSearchResource(Resource):
    id = fields.CharField(attribute='id')
    submitted_on = fields.CharField(attribute='submitted_on')
    url = fields.CharField(attribute='url')
    referer = fields.CharField(attribute='referer')
    useragent = fields.CharField(attribute='user_agent', null=True, blank=True)
    proxy = fields.CharField(attribute='proxy', null=True, blank=True)
    owner = fields.CharField(attribute='owner')
    shared_with = fields.ListField('shared_with')
    status = fields.IntegerField(attribute='status')


    def obj_get_list(self, request=None, **kwargs):
        # you have to do this if you want to use request in get_object_list
        if not request:
            request = kwargs['bundle'].request
        return self.get_object_list(request)

    def get_object_list(self, request):

        # makes sure text indexes are set
        db.analysiscombo.create_index([("$**", pymongo.TEXT)],
                                      default_language="en",
                                      language_override="en")

        search_query = request.GET.get('search')
        results = []

        if search_query:

            tree = advanced_search.search(search_query)  # Make Abstract syntax tree
            if tree:
                query = advanced_search.get_query(tree)  # Create Q query from AST
                mongo_result = [str(x['_id']) for x in
                                list(db.analysiscombo.find(query))]  # get object IDs of valid scans

            else:  # problem with parser (string can be in wrong format )
                return results
        else:  # no string detected for search
            return results

        # Only show tasks that belong to the current user, or are public, or are shared with a group this user belongs to.
        tasks = Task.objects.filter(
            Q(user__exact=request.user) |
            Q(sharing_model__exact=SHARING_MODEL_PUBLIC) |
            (Q(sharing_model__exact=SHARING_MODEL_GROUPS) & Q(sharing_groups__in=request.user.groups.all()))
        )

        # Now apply the filter of valid mongo Objects IDs Advanced search
        tasks = [task for task in tasks if task.object_id in mongo_result]

        tasks = set(tasks)  # Make the task list unique for scans within Multiple groups

        for p in tasks:
            new_obj = Object()
            new_obj.id = p.id
            new_obj.submitted_on = p.submitted_on
            new_obj.url = p.url
            new_obj.referer = p.referer
            new_obj.useragent = p.useragent
            new_obj.proxy = p.proxy
            new_obj.owner = p.user.username
            groups = []
            for group in p.sharing_groups.all():
                groups.append(group.name)
            new_obj.shared_with = groups
            new_obj.status = p.status
            results.append(new_obj)

        return results

    class Meta:
        resource_name = 'advancedsearch'
        collection_name = 'advancedsearch'
        allowed_methods = ['get']
        authentication = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        authorization = DjangoAuthorization()
        include_resource_uri = False
        object_class = Object

"""
Resources for MongoDB models
"""

class AnalysisResource(MongoDBResource):
    id          = fields.CharField(attribute="_id")
    thug        = fields.DictField(attribute="thug", null=True)
    timestamp   = fields.DateTimeField(attribute="timestamp")
    url_id      = fields.CharField(attribute="url_id")

    class Meta:
        resource_name   = 'analysis'
        authentication  = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        authorization   = OwnAndSharedAnalysesOnlyNonRelAuthorization()
        allowed_methods = ['get']
        object_class    = Document
        collection      = "analyses"
        detail_uri_name = "_id"

class UrlResource(MongoDBResource):
    id          = fields.CharField(attribute="_id")
    url         = fields.CharField(attribute="url")

    class Meta:
        resource_name   = 'url'
        authentication  = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        authorization   = OwnAndSharedUrlsOnlyNonRelAuthorization()
        allowed_methods = ['get']
        object_class    = Document
        collection      = "urls"
        detail_uri_name = "_id"
        filtering       = {
            'analysis_id': ['exact'],
        }

class BehaviorResource(MongoDBResource):
    id          = fields.CharField(attribute="_id")
    analysis_id = fields.CharField(attribute="analysis_id")
    timestamp   = fields.DateTimeField(attribute="analysis_id")
    method      = fields.CharField(attribute="method", null=True)
    cve         = fields.CharField(attribute="cve", null=True)
    description = fields.CharField(attribute="description", null=True)

    class Meta:
        resource_name   = 'behavior'
        authentication  = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        authorization   = OwnAndSharedObjectsOnlyNonRelAuthorization()
        allowed_methods = ['get']
        object_class    = Document
        collection      = "behaviors"
        detail_uri_name = "_id"
        filtering       = {
            'analysis_id': ['exact'],
        }

class ConnectionResource(MongoDBResource):
    id          = fields.CharField(attribute="_id")
    analysis_id = fields.CharField(attribute="analysis_id")
    chain_id    = fields.CharField(attribute="chain_id")
    source_id   = fields.CharField(attribute="source_id")
    destination_id = fields.CharField(attribute="destination_id")
    method      = fields.CharField(attribute="method", null=True)
    flags       = fields.DictField(attribute="flags", null=True)

    class Meta:
        resource_name   = 'connection'
        authentication  = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        authorization   = OwnAndSharedObjectsOnlyNonRelAuthorization()
        allowed_methods = ['get']
        object_class    = Document
        collection      = "connections"
        detail_uri_name = "_id"
        filtering       = {
            'analysis_id': ['exact'],
        }

class LocationResource(MongoDBResource):
    id          = fields.CharField(attribute="_id")
    analysis_id = fields.CharField(attribute="analysis_id")
    url_id      = fields.CharField(attribute="url_id")
    content_id  = fields.CharField(attribute="content_id")
    content_type = fields.CharField(attribute="content_type", null=True)
    mime_type   = fields.CharField(attribute="mime_type", null=True)
    flags       = fields.DictField(attribute="flags", null=True)
    md5         = fields.CharField(attribute="md5", null=True)
    sha256      = fields.CharField(attribute="sha256", null=True)
    size        = fields.IntegerField(attribute="size", null=True)

    class Meta:
        resource_name   = 'location'
        authentication  = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        authorization   = OwnAndSharedObjectsOnlyNonRelAuthorization()
        allowed_methods = ['get']
        object_class    = Document
        collection      = "locations"
        detail_uri_name = "_id"
        filtering       = {
            'analysis_id': ['exact'],
        }

class CodeResource(MongoDBResource):
    id          = fields.CharField(attribute="_id")
    analysis_id = fields.CharField(attribute="analysis_id")
    language    = fields.CharField(attribute="language", null=True)
    method      = fields.CharField(attribute="method", null=True)
    relationship = fields.CharField(attribute="relationship", null=True)
    snippet     = fields.CharField(attribute="snippet", null=True)

    class Meta:
        resource_name   = 'code'
        authentication  = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        authorization   = OwnAndSharedObjectsOnlyNonRelAuthorization()
        allowed_methods = ['get']
        object_class    = Document
        collection      = "codes"
        detail_uri_name = "_id"
        filtering       = {
            'analysis_id': ['exact'],
        }

class SampleResource(MongoDBResource):
    id          = fields.CharField(attribute="_id")
    analysis_id = fields.CharField(attribute="analysis_id")
    sample_id   = fields.CharField(attribute="sample_id")
    url_id      = fields.CharField(attribute="url_id")
    type        = fields.CharField(attribute="type", null=True)
    md5         = fields.CharField(attribute="md5", null=True)
    sha1        = fields.CharField(attribute="sha1", null=True)
    imphash     = fields.CharField(attribute="imphash", null=True)

    class Meta:
        resource_name   = 'sample'
        authentication  = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        authorization   = OwnAndSharedObjectsOnlyNonRelAuthorization()
        allowed_methods = ['get']
        object_class    = Document
        collection      = "samples"
        detail_uri_name = "_id"
        filtering       = {
            'analysis_id': ['exact'],
        }

class CertificateResource(MongoDBResource):
    id          = fields.CharField(attribute="_id")
    analysis_id = fields.CharField(attribute="analysis_id")
    url_id      = fields.CharField(attribute="url_id")
    certificate = fields.CharField(attribute="certificate")

    class Meta:
        resource_name   = 'certificate'
        authentication  = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        authorization   = OwnAndSharedObjectsOnlyNonRelAuthorization()
        allowed_methods = ['get']
        object_class    = Document
        collection      = "certificates"
        detail_uri_name = "_id"
        filtering       = {
            'analysis_id': ['exact'],
        }

class ExploitResource(MongoDBResource):
    id          = fields.CharField(attribute="_id")
    analysis_id = fields.CharField(attribute="analysis_id")
    url_id      = fields.CharField(attribute="url_id")
    module      = fields.CharField(attribute="module", null=True)
    cve         = fields.CharField(attribute="cve", null=True)
    description = fields.CharField(attribute="description", null=True)
    data        = fields.DictField(attribute="data", null=True)

    class Meta:
        resource_name   = 'exploit'
        authentication  = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        authorization   = OwnAndSharedObjectsOnlyNonRelAuthorization()
        allowed_methods = ['get']
        object_class    = Document
        collection      = "exploits"
        detail_uri_name = "_id"
        filtering       = {
            'analysis_id': ['exact'],
        }

class GraphResource(MongoDBResource):
    id          = fields.CharField(attribute="_id")
    analysis_id = fields.CharField(attribute="analysis_id")
    graph       = fields.CharField(attribute="graph", null=True)

    class Meta:
        resource_name   = 'graph'
        authentication  = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        authorization   = OwnAndSharedObjectsOnlyNonRelAuthorization()
        allowed_methods = ['get']
        object_class    = Document
        collection      = "graphs"
        detail_uri_name = "_id"
        filtering       = {
            'analysis_id': ['exact'],
        }

class ComboResource(MongoDBResource):
    id          = fields.CharField(attribute="_id")
    # frontend_id = fields.CharField(attribute="frontend_id")
    thug        = fields.DictField(attribute="thug", null=True)
    timestamp   = fields.CharField(attribute="timestamp")
    connections      = fields.ListField(attribute="connections")
    exploits      = fields.ListField(attribute="exploits")
    behaviors      = fields.ListField(attribute="behaviors")
    codes      = fields.ListField(attribute="codes")
    maec11      = fields.ListField(attribute="maec11")
    certificates      = fields.ListField(attribute="certificates")
    url_map      = fields.ListField(attribute="url_map")
    locations      = fields.ListField(attribute="locations")
    samples      = fields.ListField(attribute="samples")
    virustotal      = fields.ListField(attribute="virustotal")
    honeyagent      = fields.ListField(attribute="honeyagent")
    androguard      = fields.ListField(attribute="androguard")
    peepdf      = fields.ListField(attribute="peepdf")
    url_map      = fields.ListField(attribute="url_map")
    flat_tree      = fields.ListField(attribute="flat_tree", null=True)

    def dehydrate(self, bundle):
        ''' Modify flat tree first add threat data and then to
            appending warning data to that.'''
        threat_data = generate_threats(bundle.data['flat_tree'])
        warning_and_theat_data = generate_warnings(threat_data)
        bundle.data['flat_tree'] = warning_and_theat_data
        bundle.data['nested_tree'] = make_nested_tree(bundle.data['flat_tree'])
        return bundle

    class Meta:
        resource_name   = 'analysiscombo'
        authentication  = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        authorization   = OwnAndSharedAnalysesOnlyNonRelAuthorization()
        object_class    = Document
        collection      = "analysiscombo"
        detail_uri_name = "_id"
        excludes = ["id",]
        include_resource_uri = False

