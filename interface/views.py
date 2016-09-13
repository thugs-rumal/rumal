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
from django.core.serializers.json import DjangoJSONEncoder
from bson import json_util

from gridfs import GridFS
from pymongo import MongoClient
from bson import ObjectId

from interface.forms import *
from interface.models import *

import requests

from django.core import serializers
from django.core.exceptions import FieldError, ObjectDoesNotExist
import pymongo

client = pymongo.MongoClient()
db = client.thug
tags_db = client.tags

SHARING_MODEL_PUBLIC = 0
SHARING_MODEL_PRIVATE = 1
SHARING_MODEL_GROUPS = 2


@login_required
def new_task(request):
    """
    Create new task for backend to do Thug analysis
    :param request: Contains Scan Information and current logged in user
    :return: Adds task to DB
    """
    context = {
        'active_tab': 'new_task',
        'form': TaskForm(request.POST or None, user=request.user),
    }

    if request.method == 'POST':
        if context['form'].is_valid():
            saved_form = context['form'].save()

            # Assign the current user to the newly created task
            saved_form.user = request.user
            if saved_form.sharing_model == SHARING_MODEL_PRIVATE:
                saved_form.sharing_groups = []
            saved_form.save()

            return HttpResponseRedirect(reverse('interface:myscans'))

    return render(request, 'interface/new_task.html', context)


@login_required
def reports(request):
    """
    Advanced search feature moved to Restful API
    Search help display guide on what operators and fields can be used
    :param request: contains string to parse
    :return: table with scans matching query
    """

    context = {
        'search': None
    }

    context['search'] = request.GET.get('search', '')

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
def my_profile(request):
    """
    Displays Groups of the currently logged in user
    :param request: User
    :return: All groups user is in
    """

    return render(request, 'interface/myprofile.html')

@login_required
def new_group(request):
    """
    Creation of a new group. Group creator is the current logged in User
    :param request: User, group name, group members
    :return:  Creation of group
    """
    context = {
        'form': NewGroupForm(request.POST or None)
    }

    # Create new Group, add group Creator
    if request.method == 'POST':
        if context['form'].is_valid():

            # Google recaptcha validation
            g_recaptcha_response = request.POST['g-recaptcha-response']
            response = recaptcha_validation(g_recaptcha_response)

            if response:

                group_name = request.POST['group_name']
                group = Group.objects.create(name=group_name)

                # add group creator
                GroupCreator.objects.create(group=group, group_creator=request.user)
                group.user_set.add(request.user)
                group.save()
                for i in request.POST.getlist('group_members'):
                     group.user_set.add(User.objects.get(pk=i))

                return HttpResponseRedirect("/myprofile/")

    return render(request, 'interface/newgroup.html', context)

@login_required
def group(request, group_id):
    """
    Group page that contains group name, List of Users, creator, and scans for the current  logged in User.
    User has to be a valid group member to be able to view this page
    Group creator can add/remove users in this group
    :param request: Current logged in user, Group Info
    :param group_id: unique Id for group
    :return: Group Info, scans and group settings
    """

    group = get_object_or_404(Group, pk=group_id)
    group_creator = GroupCreator.objects.get(group=group).group_creator
    context = {
        'scans': None,
        'number_of_scans': None,
        'name': None,
        'members': None,
        'admin': False,
        'creator': None,
        'user_typeahead': None
    }

    # check for valid group user
    if request.user in group.user_set.all():
        context['scans'] = json_util.dumps(Task.objects.filter(sharing_groups=group).values())
        context['number_of_scans'] = len(Task.objects.filter(sharing_groups=group).values())
        context['name'] = group.name
        context['members'] = json_util.dumps([g.username for g in group.user_set.all()])
        context['creator'] = json_util.dumps(group_creator.username)
        context['user_typeahead'] = json_util.dumps([user.username for user in User.objects.all()])

    # User admin has privileges to add/remove users
    if request.user == group_creator:
        context['admin'] = True

    # Modification of Users (add/remove)
    if request.method == 'POST':
        if TagForm(request.POST).is_valid():
            users = request.POST['users'].split(',')
            # Add
            for i in users:
                try:
                    user = User.objects.get(username=i)
                    group.user_set.add(user)
                except ObjectDoesNotExist:  # Catch Invalid user names
                    pass
            # Remove
            for i in group.user_set.all():
                if i == group_creator:
                    continue
                if i.username not in users:
                    group.user_set.remove(i)

            return HttpResponseRedirect("/group/" + group_id + '/')

    return render(request, 'interface/group.html', context)


@login_required
def report(request, task_id):
    """
    Displays Scan results to User. Current Logged in User as the be valid (with in group, public, creator or private)
    Contains comments for selected node.
    Tags for a scan
    Scan owner can change scans sharing model
    :param request: Current logged in user, tags, comments and scan settings
    :param task_id: Unique ID for scan
    :return:
    """
    task = get_object_or_404(Task, pk=task_id)
    context = {
        'task': None,
        'bookmarked': False,
        'authorisation': False,
        'comment_form': CommentForm(request.POST or None),
        'settings_form': ScanSettingsForm(request.POST or None, user=request.user),
        'tags': None,
        'typeahead': 'null'
    }

    if request.method == 'POST':

        # Post comment
        if context['comment_form'].is_valid():

            # Google recaptcha validation
            g_recaptcha_response = request.POST['g-recaptcha-response']
            response = recaptcha_validation(g_recaptcha_response)

            if response:
                # comment authorisation
                if task.sharing_model is SHARING_MODEL_PUBLIC or request.user == task.user or check_group(request, task):
                    save_comment(context, request, task)
            return HttpResponseRedirect("/report/" + task_id+'/')

        elif context['settings_form'].is_valid():
            # Modify settings of scan
            if request.user == task.user:  # only owner can modify
                task.sharing_model = int(context['settings_form'].cleaned_data['sharing_model'])
                task.sharing_groups = context['settings_form'].cleaned_data['sharing_groups']
                if task.sharing_model == SHARING_MODEL_PRIVATE:
                    task.sharing_groups = []
                task.save()
            return HttpResponseRedirect("/report/" + task_id + '/')

        elif TagForm(request.POST).is_valid():  # Add scan tags

            if task.sharing_model is SHARING_MODEL_PUBLIC or request.user == task.user or check_group(request, task):
                create_or_modify_tag(task_id, request.POST['tags'])
            return HttpResponseRedirect("/report/" + task_id + '/')

        else:
            return render(request, 'interface/report.html', context)

    # If scan is public or used is allowed to view scan
    if task.sharing_model is SHARING_MODEL_PUBLIC or request.user == task.user or check_group(request, task) :
        context['task'] = task
        context['authorisation'] = True
        if request.user in task.star.all():
            context['bookmarked'] = True

        # Tag data for scan
        try:
            tags = db.analysiscombo.find_one({'frontend_id': task_id})['tags']
            context['tags'] = ','.join(tags)
        except KeyError:  # No tags exists currently, pass in empty value
            context['tags'] = ''
        except TypeError:  # Mongo error tags is not found
            pass

        # typeahead data
        try:
            tyepahead_data = tags_db.tags.find_one()['tags']
            if tyepahead_data:
                context['typeahead'] = json.dumps(tyepahead_data)
        except KeyError:  # Mongo error
            pass
        except TypeError:  # Mongo error tags is not found
            pass

    return render(request, 'interface/report.html', context)


def create_or_modify_tag(task_id, tags):
    """
    Add/remove scan tags
    :param task_id: Unique ID for scan
    :param tags: list of current tags
    :return:
    """
    # Set tags for selected scan
    tags = tags.split(',')
    db.analysiscombo.update_one({"frontend_id": task_id},  {"$set": {"tags": tags}})
    # add tag for typeahead
    [tags_db.tags.update_one({}, {'$addToSet': {'tags': tag}}, upsert=True) for tag in tags]


def save_comment(context, request, task):
    """
    New comment for node
    :param context: Post request containing comment info
    :param request: Current logged in user
    :param task: task comment was posted on
    :return:
    """
    saved_form = context['comment_form'].save()

    # Assign the current user to the newly created comment
    saved_form.user = request.user
    saved_form.task = task
    saved_form.node = request.POST['node']
    saved_form.save()

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
