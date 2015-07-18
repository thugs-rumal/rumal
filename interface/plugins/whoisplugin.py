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

import sys
import os.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

from plug import *
import tldextract
import pythonwhois


class WhoisPlugin(PluginBase):
    @property
    def dependencies(self):
        """List of dependencies - put class names of required plugins here.
           Return blank list if none."""
        return []

    @property
    def module_dependencies(self):
        """List of non-standard lib module dependencies
           - put module names as keys and versions as
           values.Return blank list if none."""
        return
        {
            "tldextract": "1.6",
            "pythonwhois": "2.4.0"
        }

    def find_domain(self, url):
        """ Find top level domain from given url"""
        ext = tldextract.extract(url)
        return ext.registered_domain

    def get_whois(self, domain):
        """ Fetch whois data for the given domain."""
        return pythonwhois.get_whois(domain)  # check for normalizations

    def run(self):
        """Run and make changes to data"""
        self.check_dependencies()
        # 2. Append all changes to x.data["flat_tree"]["url_link/node"]["plugin_name"]
        domain_whois_map = {}  # keys are domain names and values contain respective whois data.
        for node in self.data["flat_tree"]:
            node_domain = self.find_domain(node["url"])
            if node_domain in domain_whois_map.keys():
                node["WhoisPlugin"] = domain_whois_map[node_domain]
            else:
                node["WhoisPlugin"] = self.get_whois(node_domain)
                domain_whois_map[node_domain] = node["WhoisPlugin"]
        # 3. Call save data
        self.save_data()
