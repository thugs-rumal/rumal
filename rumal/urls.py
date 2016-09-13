#!/usr/bin/env python
#
# urls.py
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

from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth.views import login, logout_then_login
from tastypie.api import Api
from interface.api import *

v1_api = Api(api_name='v1')
v1_api.register(UserResource())
v1_api.register(CurrentUserResource())
v1_api.register(GroupResource())
v1_api.register(ProxyResource())
v1_api.register(TaskResource())
v1_api.register(AnalysisResource())
v1_api.register(UrlResource())
v1_api.register(BehaviorResource())
v1_api.register(ConnectionResource())
v1_api.register(LocationResource())
v1_api.register(CodeResource())
v1_api.register(SampleResource())
v1_api.register(CertificateResource())
v1_api.register(ExploitResource())
v1_api.register(GraphResource())
v1_api.register(ComboResource())
v1_api.register(CommentResource())

urlpatterns = (
    # Admin views
    url(r'^admin/', include(admin.site.urls)),
    url(r'^login/$', login, name="login"),
    url(r'^logout/$', logout_then_login, name="logout"),

    # APIs
    url(r'^api/', include(v1_api.urls)),

    # Apps
    url(r'', include('interface.urls', namespace="interface", app_name="interface"))
)
