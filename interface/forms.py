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
    class Meta:
        model       = Task
        exclude     = ['user', 'submitted_on', 'started_on', 'completed_on', 'status', 'plugin_status']
