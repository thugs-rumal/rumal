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
# Author:   Pietro Delsante <pietro.delsante@gmail.com>
#           The Honeynet Project
#

from django.contrib import admin
from .models import Proxy, Task

# Register your models here.

class TaskAdmin(admin.ModelAdmin):
    #list_display = ['__unicode__', 'proxy', 'broken_url']
    list_display = ['proxy', 'broken_url', 'no_javaplugin']
    date_hierarchy = 'submitted_on'
    actions = ['add_broken_url', 'remove_broken_url',
        'enable_javaplugin', 'disable_javaplugin',
        'sharingmodel_groups', 'sharingmodel_private',
        'sharingmodel_public']
    def add_broken_url(self, request, queryset):
        queryset.update(broken_url = True)
    add_broken_url.short_description = 'Add Broken Url tag'

    def remove_broken_url(self, request, queryset):
        queryset.update(broken_url = False)
    remove_broken_url.short_description = 'Remove Broken Url tag'

    def enable_javaplugin(self, request, queryset):
        queryset.update(no_javaplugin = True)
    enable_javaplugin.short_description = 'Enable Java Plugins'

    def disable_javaplugin(self, request, queryset):
        queryset.update(no_javaplugin = False)
    disable_javaplugin.short_description = 'Disable Java Plugins'

    def sharingmodel_groups(self, request, queryset):
        queryset.update(sharing_model = 2)
    sharingmodel_groups.short_description = 'Share with Groups'

    def sharingmodel_private(self, request, queryset):
        queryset.update(sharing_model = 1)
    sharingmodel_private.short_description = 'Make Private'

    def sharingmodel_public(self, request, queryset):
        queryset.update(sharing_model = 0)
    sharingmodel_public.short_description = 'Make Public'

admin.site.register(Proxy)
admin.site.register(Task, TaskAdmin)
