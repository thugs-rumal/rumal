#!/usr/bin/env python
#
# admin.py
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

from django.contrib import admin
from .models import Proxy, Task, PluginTask, Comment, Group, GroupCreator
from django.contrib.auth.admin import GroupAdmin
from django.core.urlresolvers import reverse

# Register your models here.

def add_broken_url(modelAdmin, request, queryset):
    queryset.update(broken_url = True)
add_broken_url.short_description = 'Add Broken Url tag'

def remove_broken_url(modelAdmin, request, queryset):
    queryset.update(broken_url = False)
remove_broken_url.short_description = 'Remove Broken Url tag'

def enable_javaplugin(modelAdmin, request, queryset):
    queryset.update(no_javaplugin = True)
add_broken_url.short_description = 'Enable Java Plugins'

def disable_javaplugin(modelAdmin, request, queryset):
    queryset.update(no_javaplugin = False)
disable_javaplugin.short_description = 'Disable Java Plugins'

def persons(self):
    return ', '.join(['<a href="%s">%s</a>' % (reverse('admin:auth_user_change', args=(x.id,)), x.username) for x in self.user_set.all().order_by('username')])
persons.allow_tags = True

class TaskAdmin(admin.ModelAdmin):
    #list_display = ['__unicode__', 'proxy', 'broken_url']
    list_display = ['proxy', 'broken_url', 'no_javaplugin']
    date_hierarchy = 'submitted_on'
    actions = [add_broken_url, remove_broken_url,
        enable_javaplugin, disable_javaplugin]

class CommentAdmin(admin.ModelAdmin):
    list_display = ['created_on', 'task', 'node', 'user', 'text']

class GroupAdmin(GroupAdmin):
    list_display = ['name', persons]
    list_display_links = ['name']

class GroupCreatorAdmin(admin.ModelAdmin):
    list_display = ['group', 'group_creator']

admin.site.register(Proxy)
admin.site.register(PluginTask)
admin.site.register(Task, TaskAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)
admin.site.register(GroupCreator, GroupCreatorAdmin)