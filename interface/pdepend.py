#!/usr/bin/env python
#
# pdepen.py
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
# NOTE: THIS IS AN INITIAL RELEASE AND IS LIKELY TO BE UNSTABLE

""" TODO: This code needs some serious restrucring """

L = []
visited = []

def nodeps(data):
    S = []
    for each in data.keys():
        if not len(data[each]):
            S.append(each)
    return S

def dependson(node, data):
    r = []
    for each in data.keys():
        for n in data[each]:
            if n == node:
                r.append(each)
    return r

def visit(node, data):
    if not node in visited:
        visited.append(node)
        for m in dependson(node, data):
            visit(m, data)
        L.append(node)

def resolve_dependencies(data):
    for node in nodeps(data):
        visit(node, data)
    return L[::-1]

