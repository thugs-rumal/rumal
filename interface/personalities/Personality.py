#!/usr/bin/env python
#
# Personality.py
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

import sys
import os
import json

class Personality(dict):
    def __init__(self):
        personalities = os.path.join(os.path.dirname(os.path.abspath(__file__)), "personalities")
        if personalities is None:
            return {}

        for root, dir, files in os.walk(personalities):
            for f in files:
                if not f.endswith('.json'):
                    continue

                name = f.split(".json")[0]
                with open(os.path.join(root, f)) as personality:
                    self[name] = json.load(personality)

