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
# Author:   Pietro Delsante <pietro.delsante AT gmail.com>
#           The Honeynet Project
#
import base64
import hexdump
import magic
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404

from gridfs import GridFS
from pymongo import MongoClient
from bson import ObjectId

from interface.forms import *
from interface.models import *

import requests

from django.core import serializers
import advanced_search
from django.core.exceptions import FieldError
import pymongo

client = pymongo.MongoClient()
db = client.thug
tags_db = client.tags

SHARING_MODEL_PUBLIC = 0
SHARING_MODEL_PRIVATE = 1
SHARING_MODEL_GROUPS = 2


@login_required
def new_task(request):
    context = {
        'active_tab': 'new_task',
        'form': TaskForm(request.POST or None),
    }

    if request.method == 'POST':
        if context['form'].is_valid():
            saved_form = context['form'].save()

            # Assign the current user to the newly created task
            saved_form.user = request.user
            saved_form.save()

            return HttpResponseRedirect(reverse('interface:myscans'))

    return render(request, 'interface/new_task.html', context)


@login_required
def reports(request):
    """
    Advanced search feature, parses string into a mongodb query, displays relevant results to user in table.
    Search help display guide on what operators and fileds can be used
    :param request: contains string to parse
    :return: table with scans matching query
    """
    # makes sure text indexes are set
    db.analysiscombo.create_index([("$**", pymongo.TEXT)],
                                  default_language="en",
                                  language_override="en")

    tasks = Task.objects
    context = {
        'active_tab': 'reports',
        'status': None,  # Error messages for advanced search
        'help': False  # Display help setting to user
    }

    if 'help' in request.get_full_path().split('/'):  # Display help aid
        context['help'] = True
        return render(request, 'interface/results.html', context)

    search_query = request.GET.get('search', '')

    if search_query:

        tree = advanced_search.search(search_query)  # Make Abstract syntax tree
        if tree:

            query = advanced_search.get_query(tree)  # Create Q query from AST
            mongo_result = [str(x['_id']) for x in list(db.analysiscombo.find(query))]  # get object IDs of valid scans

        else:  # problem with parser (string can be in wrong format )
            context['status'] = 'Could not make AST'
            return render(request, 'interface/results.html', context)
    else:  # no string detected for search
        context['status'] = 'Empty search'
        return render(request, 'interface/results.html', context)

    #  Only show tasks that belong to the current user, or are public, or are shared with a group this user belongs to.
    tasks = tasks.filter(
        Q(user__exact=request.user) |
        Q(sharing_model__exact=SHARING_MODEL_PUBLIC) |
        (Q(sharing_model__exact=SHARING_MODEL_GROUPS) & Q(sharing_groups__in=request.user.groups.all()))
        )

    # Now apply the filter of valid mongo Objects IDs Advanced search
    tasks = [task for task in tasks if task.object_id in mongo_result]

    context['tasks'] = serializers.serialize('json', tasks)
    context['total'] = len(tasks)

    return render(request, 'interface/results.html', context)


@login_required
def my_scans(request):
    tasks = Task.objects
    user_tasks = tasks.filter(user=request.user)
    public_user_tasks = user_tasks.filter(sharing_model__exact=SHARING_MODEL_PUBLIC)
    private_user_tasks = user_tasks.filter(sharing_model__exact=SHARING_MODEL_PRIVATE)
    star_tasks = request.user.star_tasks.all()
    stats = {
        'public': len(public_user_tasks),
        'private': len(private_user_tasks),
        'star': len(star_tasks)
    }
    context = {
        'stats': stats,
    }
    return render(request, 'interface/myscans2.html', context)


@login_required
def report(request, task_id):
    task = get_object_or_404(Task, pk=task_id)
    context = {
        'task': None,
        'bookmarked': False,
        'authorisation': False,
        'comment_form': CommentForm(request.POST or None),
        'settings_form': ScanSettingsForm(request.POST or None),
        'tags': None
    }

    if request.method == 'POST':

        # Post comment
        if context['comment_form'].is_valid():

            # Google recaptcha validation
            g_recaptcha_response = request.POST['g-recaptcha-response']
            response = recaptcha_validation(g_recaptcha_response)

            if response:
                # comment authorisation
                if task.sharing_model is SHARING_MODEL_PUBLIC or request.user == task.user:
                    save_comment(context, request, task)
            return HttpResponseRedirect("/report/" + task_id+'/')

        elif context['settings_form'].is_valid():
            # Modify settings of scan
            if request.user == task.user:  # only owner can modify
                task.sharing_model = int(context['settings_form'].cleaned_data['sharing_model'])
                task.save()
            return HttpResponseRedirect("/report/" + task_id + '/')

        elif TagForm(request.POST).is_valid():  # Add scan tags
            if request.user == task.user:
                create_or_modify_tag(task_id, request.POST['tags'])
            return HttpResponseRedirect("/report/" + task_id + '/')

        else:
            return render(request, 'interface/report.html', context)

    # If scan is public or used is allowed to view scan
    if task.sharing_model is SHARING_MODEL_PUBLIC or request.user == task.user:
        context['task'] = task
        context['authorisation'] = True
        if request.user in task.star.all():
            context['bookmarked'] = True
        tags = tags_db.scantags.find_one({'_id': task_id})
        if tags:
            context['tags'] = tags['tags']

    return render(request, 'interface/report.html', context)

def create_or_modify_tag(task_id, tags):
    tags_db.scantags.update_one({"_id": task_id},  {"$set": {"tags": tags}}, upsert=True)

def save_comment(context, request, task):
    saved_form = context['comment_form'].save()

    # Assign the current user to the newly created comment
    saved_form.user = request.user
    saved_form.task = task
    saved_form.node = request.POST['node']
    saved_form.save()


def recaptcha_validation(g_recaptcha_response):
    params = {
        'secret': RECAPTCHA_SECRET_KEY,
        'response': g_recaptcha_response,
    }
    verify_rs = requests.get(URL, params=params, verify=True)
    verify_rs = verify_rs.json()
    return bool(verify_rs.get("success", False))


@login_required
def json_tree_graph(request, analysis_id=None):
    # TODO: migrate this view to the APIs? (Not sure if it's easily feasible)
    # TODO: use NetworkX to construct the graph?
    if not analysis_id:
        raise Http404("Analysis not found")
    graph = {
        'analysis_id': analysis_id,
        'graph': {
            'directed': True,
            'nodes': {}
        }
    }
    root_link = graph_get_root_node(analysis_id)
    root_node = graph_populate_node(analysis_id, root_link['source_id'])
    graph['graph']['nodes'] = graph_get_children(analysis_id, root_node)
    return JsonResponse(graph)


@login_required
def star_view(request):
    task_id = int(request.GET['taskId'])
    task = get_object_or_404(Task, pk=task_id)
    if request.user in task.star.all():
        task.star.remove(request.user)
    else:
        task.star.add(request.user)
    return HttpResponse(1 if request.user in task.star.all() else 0)


def content(request, content_id=None):
    # TODO: migrate this view to the APIs? (would need a GridFSResource)
    if not content_id:
        raise Http404("Content not found")

    if not isinstance(content_id, ObjectId):
        try:
            content_id = ObjectId(content_id)
        except:
            raise Http404("Content not found")

    dbfs = MongoClient().thugfs
    fs = GridFS(dbfs)

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

def raw_content(request, content_id=None):
    # TODO: migrate this view to the APIs? (would need a GridFSResource)
    if not content_id:
        raise Http404("Content not found")

    if not isinstance(content_id, ObjectId):
        try:
            content_id = ObjectId(content_id)
        except:
            raise Http404("Content not found")

    dbfs = MongoClient().thugfs
    fs = GridFS(dbfs)

    fo = fs.get(content_id)
    try:
        content = base64.b64decode(fo.read())
    except:
        raise Http404("Content not found")

    mime = magic.from_buffer(content, mime=True)

    response = HttpResponse(content, content_type=mime)
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(fo.filename or fo.md5)
    return response
