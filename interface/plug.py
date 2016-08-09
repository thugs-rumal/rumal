#!/usr/bin/env python
#
# plug.py
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
# Author:   Tarun Kumar <reach.tarun.here AT gmail.com>
#

import abc
import os
import sys

from ConfigParser import SafeConfigParser
from django.conf import settings

class UnmetDependencyError(Exception):
    value = "Dependency %s was not met."


class PluginBase(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def dependencies(self):
        """List of dependencies - put class names of required plugins here.
           Return blank list if none."""
        return []

    @abc.abstractproperty
    def module_dependencies(self):
        """List of non-standard lib module dependencies
           - put module names as keys and versions as
           values.Return blank list if none."""
        return {}

    def input_run(self, data):
        """Adds data to object and calls self.config and self.run"""
        self.data = data
        self.get_config()
        if not self.config_dict['enabled']:
            return False

        return self.run()

    def get_config(self):
        """Gets config file data and stores it under self.config of object instance"""
        parser = SafeConfigParser()
        self.config_dict = {}
        plugins_conf_dir = os.path.abspath(os.path.join(settings.BASE_DIR, 'conf', 'plugins'))
        conf_path = os.path.join(plugins_conf_dir, '{}.conf'.format(self.__class__.__name__))
        if os.path.isfile(conf_path):
            self.config_dict['enabled'] = True
            parser.read(conf_path)
            for section_name in parser.sections():
                section_content = {}
                for name, value in parser.items(section_name):
                    section_content[name] = value
                self.config_dict[section_name] = section_content
        else:
            self.config_dict['enabled'] = False

    def save_data(self):
        """Add to plugins list and return modified data."""
        if "Plugins" not in self.data.keys():
            self.data["Plugins"] = []
        if self.__class__.__name__ not in self.data["Plugins"]:
            self.data["Plugins"].append(self.__class__.__name__)
        return self.data

    def check_dependencies(self):
        """Check if all the dependencies are met."""
        for x in self.dependencies:
            if x not in self.data["Plugins"]:
                raise UnmetDependencyError(x)

    @abc.abstractmethod
    def run(self):
        """Run and make changes to data"""
        # 1. Call check for dependencies
        self.check_dependencies()
        # 2. Append all changes to x.data["flat_tree"]["url_link/node"]["plugin_name"]
        # 3. Call save data
        self.save_data()

    def search(self):
        pass

def find_plugins():
    '''find all files in the plugin directory and imports them'''
    plugin_dir = os.path.abspath(os.path.join(settings.BASE_DIR, 'interface', 'plugins'))
    plugin_files = [x[:-3] for x in os.listdir(plugin_dir) if x.endswith(".py") and x != "__init__.py"]
    sys.path.insert(0, plugin_dir)
    for plugin in plugin_files:
      mod = __import__(plugin)

def register_plugins():
    '''Register all class based plugins.

     Uses the fact that a class knows about all of its subclasses
     to automatically initialize the relevant plugins
    '''
    # Config directory location
    plugins_conf_dir = os.path.abspath(os.path.join(settings.BASE_DIR, 'conf', 'plugins'))

    all_plugins = {}
    for plugin in PluginBase.__subclasses__():
        # Only return plugins that have a config file
        conf_path = os.path.join(plugins_conf_dir, '{}.conf'.format(plugin.__name__))
        if os.path.isfile(conf_path):
            all_plugins[plugin.__name__] = plugin

    return all_plugins

def init_plugins():
    '''simple plugin initializer
    '''
    find_plugins()
    return register_plugins()
