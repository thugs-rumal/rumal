#!/usr/bin/env python
#
# highlights.py
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
# Author:   Tarun Kumar <reach.tarun.here@gmail.com>
#

import datetime

def generate_threats(data):
    ''' wrapper function to call functions that mark threats'''
    for node in data:
        node['threats'] = []
        exploit_threats_output = exploit_threats(node)
        if exploit_threats_output:
            node['threats'].extend()
        # similarly other function calls according to methods for
        # finding threats and use extend and append as required.
    return data

def generate_warnings(data):
    ''' wrapper function to call functions that mark warnings'''
    for node in data:
        node['warnings'] = []
        new_domain_warning_output = new_domain_warning(node)
        if new_domain_warning_output:
            node['warnings'].append(new_domain_warning_output)
        # similarly other function calls according to methods for
        # finding warnings and use extend and append as required.
    return data

# Threat Functions

def exploit_threats(node):
    output = []
    for exploits in node['exploits']:
        threat = {}
        threat['type'] = 'exploit'
        threat['details'] = {
        'Module' : exploit['module']
        'Description' : exploit['description']
        'CVE' : exploit['cve']
        'Additional Info' : exploit['data']
        }
        output.append(threat)
    return output

# Warning Functions

def new_domain_warning(node):
    ''' Add a new domain warning to each node's warning list'''
    if node['WhoisPlugin']:
        domain_creation_time = node['WhoisPlugin']['creation_time'][-1]
        current_time = datetime.datetime.now()
        time_diff = current_time - domain_creation_time
        if time_diff.days < 30:
            warning['type'] = 'Recent Domain'
            warning['details'] = {
            'Message' : 'The domain was registered less than 30 days ago.',
            'Registrar' : node['WhoisPlugin']['registrar'],
            }
        return warning
    else:
        return False

