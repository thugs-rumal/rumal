#!/usr/bin/env python
#
# utils.py
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

from DOM.Personality import Personality
from pymongo import Connection
from bson import ObjectId
from urlparse import urlparse

db = Connection().thug

def get_personalities():
    return [('', 'Default')] + \
        sorted([(x, y['description'].replace('\t', ' ')) for x, y in Personality().iteritems()], key=lambda x: x[1])

def graph_get_root_node(analysis_id):
    return db.connections.find({"analysis_id": ObjectId(analysis_id)}).sort("chain_id")[0]

def graph_populate_node(analysis_id, url_id):
    if not isinstance(analysis_id, ObjectId):
        analysis_id = ObjectId(analysis_id)
    url         = db.urls.find_one({"_id": url_id})
    location    = db.locations.find_one({"analysis_id": analysis_id, "url_id": url_id}) or {}
    exploits    = [x for x in db.exploits.find({"analysis_id": analysis_id, "url_id": url_id})]

    for key, value in location.iteritems():
        if isinstance(value, ObjectId):
            location[key] = str(value)

    for exploit in exploits:
        for key, value in exploit.iteritems():
            if isinstance(value, ObjectId):
                exploit[key] = str(value)

    node = {
        'url_id'    : str(url_id),
        'url'       : url and url['url'] or '-',
        'domain'    : url and urlparse(url['url']).hostname or '-',
        'location'  : location and location or {},
        'exploits'  : exploits,
        'children'  : []
    }
    return node

def graph_get_children(analysis_id, parent):
    if not isinstance(analysis_id, ObjectId):
        analysis_id = ObjectId(analysis_id)
    if not isinstance(parent['url_id'], ObjectId):
        url_id = ObjectId(parent['url_id'])
    else:
        url_id = parent['url_id']
    for connection in db.connections.find({"analysis_id": analysis_id, "source_id": url_id}):
        node = graph_populate_node(analysis_id, connection['destination_id'])
        node = graph_get_children(analysis_id, node)
        parent['children'].append(node)

    if not parent['children']:
        parent.pop('children')
    return parent

def is_text(mime):
    if mime.startswith('text/'):
        return True

    if mime in ['application/xml']:
        return True

    return False

def make_nested_tree(flat_tree):
    for node in reversed(flat_tree):
        if node['parent'] != None:
            parent_node = flat_tree[node['parent']]
            if 'children' not in parent_node.keys():
                parent_node['children'] = []
            parent_node['children'].append(node)
    return flat_tree[0]
