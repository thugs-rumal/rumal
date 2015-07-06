#!/usr/bin/env python
#
# whoisplugin.py
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

from interface.plug import *

class WhoisPlugin(PluginBase):  
    @property
    def dependencies(self):
        """List of dependencies - put class names of required plugins here.
           Return blank list if none."""
        return []

    def find_domain(self,url):
        pass

    def get_whois(self,domain):
        pass

    def run(self):
        """Run and make changes to data"""
        self.check_dependencies()
        #2. Append all changes to x.data["flat_tree"]["url_link/node"]["plugin_name"]
        domain_whois_map = {}
        for node in self.data["flat_tree"]:
            node_domain = self.find_domain(node["url"])
            if node_domain in domain_whois_map.keys():
                node["WhoisPlugin"] = domain_whois_map[node_domain]
            else:
                node["WhoisPlugin"] = self.get_whois(node_domain)
                domain_whois_map[node_domain] = node["WhoisPlugin"]
        #3. Call save data
        self.save_data()
