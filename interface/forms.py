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
# Author:   Pietro Delsante <pietro.delsante AT gmail.com>
#           The Honeynet Project
#

import re
from django import forms
from interface.models import *


class TaskForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        current_user = kwargs.pop('user')
        super(TaskForm, self).__init__(*args, **kwargs)
        self.fields['sharing_groups'].queryset = current_user.groups.all()

    class Meta:
        model       = Task
        exclude     = ['user', 'submitted_on', 'started_on', 'completed_on', 'status', 'plugin_status']


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        exclude = ['user', 'created_on']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'comment-input', 'style': 'width:100%;'}),
        }


class ScanSettingsForm(forms.Form):

    def __init__(self, *args, **kwargs):
        current_user = kwargs.pop('user')
        super(ScanSettingsForm, self).__init__(*args, **kwargs)
        self.fields['sharing_groups'].queryset = current_user.groups.all()

    sharing_model = forms.ChoiceField(choices=SHARING_MODEL_CHOICES)
    sharing_groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(), required=False)

class TagForm(forms.Form):
    tags = forms.TextInput()


class NewGroupForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(NewGroupForm, self).__init__(*args, **kwargs)
        self.fields['group_members'].widget.attrs['id'] = 'select_user'
        self.fields['group_name'].widget.attrs['class'] = 'form-control'



    group_name = forms.CharField(required=True)
    group_members = forms.ModelMultipleChoiceField(queryset=User.objects.all())


