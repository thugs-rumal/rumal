#!/usr/bin/env python
#
# views.py
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

import base64
import hexdump
import magic
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse, Http404
from gridfs import GridFS
from pymongo import Connection
from bson import ObjectId
from django.views.decorators.csrf import csrf_protect

from interface.forms import *
from interface.models import *

@csrf_protect
@login_required
def new_task(request):
    context = {
        'active_tab': 'new_task',
        'form'      : TaskForm(request.POST or None)
    }

    if request.method == 'POST':
        if context['form'].is_valid():
            saved_form = context['form'].save()

            # Assign the current user to the newly created task
            saved_form.user = request.user
            saved_form.save()

            return HttpResponseRedirect(reverse('interface:report', kwargs={'task_id': saved_form.id}))

    return render(request, 'interface/new_task.html', context)

@login_required
def reports(request, status='any', pagination_start=0, pagination_len=50):
    pagination_start    = int(pagination_start)
    pagination_len      = int(pagination_len)
    #if not status:
        #status = 'any'
    #if not pagination_start:
        #pagination_start = 0
    #if not pagination_len:
        #pagination_len = 50

    context = {
        'active_tab': 'reports',
    }
    tasks = Task.objects
    if status == 'new':
        tasks = tasks.filter(status__exact=STATUS_NEW)
    elif status == 'processing':
        tasks = tasks.filter(status__exact=STATUS_PROCESSING)
    elif status == 'failed':
        tasks = tasks.filter(status__exact=STATUS_FAILED)
    elif status == 'completed':
        tasks = tasks.filter(status__exact=STATUS_COMPLETED)

    # Only show tasks that belong to the current user, or are public, or are shared with a group this user belongs to.
    tasks = tasks.filter(
        Q(user__exact = request.user) |
        Q(sharing_model__exact=SHARING_MODEL_PUBLIC) |
        (Q(sharing_model__exact=SHARING_MODEL_GROUPS) & Q(sharing_groups__in=request.user.groups.all()))
        )

    context['tasks']    = tasks.order_by('-id')[pagination_start:pagination_start+pagination_len]
    context['total']    = tasks.count()
    context['start']    = pagination_start
    context['len']      = pagination_len

    return render(request, 'interface/results.html', context)

@login_required
def report(request, task_id):
    context = {
        'active_tab': 'reports',
        'task'      : get_object_or_404(Task, pk=task_id)
    }

    return render(request, 'interface/result.html', context)

@login_required
def json_tree_graph(request, analysis_id=None):
    # TODO: migrate this view to the APIs? (Not sure if it's easily feasible)
    # TODO: use NetworkX to construct the graph?
    if not analysis_id:
        raise Http404("Analyis not found");
    graph = {
        'analysis_id': analysis_id,
        'graph': {
            'directed': True,
            'nodes': {}
        }
    }
    root_link   = graph_get_root_node(analysis_id)
    root_node   = graph_populate_node(analysis_id, root_link['source_id'])
    graph['graph']['nodes'] = graph_get_children(analysis_id, root_node)
    return JsonResponse(graph)

def content(request, content_id=None):
    # TODO: migrate this view to the APIs? (would need a GridFSResource)
    if not content_id:
        raise Http404("Content not found")

    if not isinstance(content_id, ObjectId):
        try:
            content_id = ObjectId(content_id)
        except:
            raise Http404("Content not found")

    dbfs    = Connection().thugfs
    fs      = GridFS(dbfs)

    try:
        content = base64.b64decode(fs.get(content_id).read())
    except:
        raise Http404("Content not found")

    hexdumped = False
    mime = magic.from_buffer(content, mime=True)
    if not is_text(mime):
        content = hexdump.hexdump(content, result='return')
        hexdumped = True

    # Ensure to use Unicode for the content, else JsonResopnse may fail
    if not isinstance(content, unicode):
        content = unicode(content, errors='ignore')

    data = {
        'content_id': str(content_id),
        'mime': mime,
        'content': content,
    }

    return JsonResponse(data)
