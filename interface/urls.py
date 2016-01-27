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
# Author:   Pietro Delsante <pietro.delsante@gmail.com>
#           The Honeynet Project
#

from django.conf.urls import url
from interface import views

urlpatterns = (
    url(r'^report/(?:(?P<task_id>\d+)/)?$', views.report, name='report'),
    url(r'^reports/$', views.reports, name='reports'),
    url(r'^myscans/$', views.my_scans, name='myscans'),
    url(r'^togglebookmark/$', views.star_view, name='star'),

    url(r'^json_tree_graph/(?:(?P<analysis_id>[\w]+)/)?$', views.json_tree_graph, name='json_tree_graph'),
    url(r'^content/(?:(?P<content_id>[\w]+)/)?$', views.content, name='content'),
    url(r'^raw_content/(?:(?P<content_id>[\w]+)/)?$', views.raw_content, name='raw_content'),

    url(r'^$', views.new_task, name='new_task'),
)
