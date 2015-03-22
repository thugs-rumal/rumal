#!/usr/bin/env python
#
# forms.py
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

from __future__ import unicode_literals
#To make Python 3 compatible
import re
from django import forms
from interface.models import *
from django.utils.translation import ugettext_lazy as _

class TaskForm(forms.ModelForm):
    error_messages = {
        'start_time_gte_completed_on': _("Start Time must be smaller than Completed On"),
        'submitted_on_gte_completed_on': _("Submission Time must be smaller than Completed On"),
        'submitted_on_gte_start_time': _("Submission Time must be smaller [or equal] than Start Time"),
        'invalid_status': _("Invalid Status")
    }

    class Meta:
        model       = Task
        exclude     = ['user', 'submitted_on', 'started_on', 'completed_on', 'status']

    def clean_status(self):
        status = self.cleaned_data.get(status, None)
        if status > 3 and status < 0:
            raise forms.ValidationError(
                self.error_messages['invalid_status'],
                code='invalid_status'
            )
        return self.cleaned_data

    def clean(self):
        cleaned_data = super(TaskForm, self).clean()
        started_on = cleaned_data.get('started_on', None)
        submitted_on = cleaned_data.get('submitted_on', None)
        completed_on = cleaned_data.get('completed_on', None)
        if completed_on:
            if started_on and started_on > completed_on:
                raise forms.ValidationError(
                    self.error_messages['start_time_gte_completed_on'],
                    code='start_time_gte_completed_on'
                )
            if submitted_on and submitted_on > completed_on:
                raise forms.ValidationError(
                    self.error_messages['submitted_on_gte_completed_on'],
                    code='submitted_on_gte_completed_on'
                )
        if started_on and submitted_on and started_on < submitted_on:
            raise forms.ValidationError(
                self.error_messages['submitted_on_gte_start_time'],
                code='submitted_on_gte_start_time'
            )
        return cleaned_data