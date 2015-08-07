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
# Author:   Pietro Delsante <pietro.delsante@gmail.com>
#           The Honeynet Project
#

from tastypie import fields
from tastypie.resources import ModelResource
from tastypie.authentication import SessionAuthentication, ApiKeyAuthentication, MultiAuthentication
from tastypie.authorization import DjangoAuthorization, ReadOnlyAuthorization
from django.contrib.auth.models import User, Group
from rumal.authorization import *

from interface.models import *
from interface.resources import MongoDBResource

from django.http import HttpRequest
"""
Resources for SQLite models
"""

class GroupResource(ModelResource):
    class Meta:
        queryset        = Group.objects.all()
        resource_name   = 'group'
        authentication  = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        authorization   = DjangoAuthorization()
        allowed_methods = ['get']
        fields          = ['id', 'name']
        ordering        = ['id', 'name']

class UserResource(ModelResource):
    class Meta:
        queryset        = User.objects.all()
        resource_name   = 'user'
        authentication  = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        authorization   = DjangoAuthorization()
        allowed_methods = ['get']
        fields          = ['id', 'username']
        ordering        = ['id', 'username']

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

    def renderDetail(self,pkval):
        request = HttpRequest()
        request.GET = {'format': 'json'}
        resp =  self.get_detail(request, pk=pkval)
        return resp.content

    class Meta:
        queryset        = Task.objects.all()
        resource_name   = 'task'
        authentication  = MultiAuthentication(SessionAuthentication(), ApiKeyAuthentication())
        authorization   = OwnAndSharedObjectsOnlyRelAuthorization()
        allowed_methods = ['get']
        include_resource_uri = False
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
    timestamp   = fields.DateTimeField(attribute="timestamp")
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

    class Meta:
        resource_name   = 'analysiscombo'
        object_class    = Document
        collection      = "analysiscombo"
        detail_uri_name = "_id"
        excludes = ["id",]
        include_resource_uri = False