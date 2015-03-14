#!/usr/bin/env python
#
# resources.py
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

from pymongo import Connection
from bson import ObjectId

from tastypie.bundle import Bundle
from tastypie.resources import Resource
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.constants import LOOKUP_SEP
from django.http import QueryDict

# TODO: See if this one is better than reinventing the wheel: http://django-tastypie-mongoengine.readthedocs.org/en/latest/

# TODO: support more QUERY_TERMS such as 'text', 'near', 'all', 'elemMatch', 'size', etc.
QUERY_TERMS = ['exact', 'ne', 'gt', 'gte', 'lt', 'lte', 'in', 'nin', 'regex', 'iregex']

db = Connection().thug

class MongoDBResource(Resource):
    """
    A base resource that allows to make CRUD operations for mongodb.
    Based on:
    - https://github.com/fatiherikli/tastypie-mongodb-resource/blob/master/tastypie_mongodb/resources.py
    - https://github.com/django-tastypie/django-tastypie/blob/master/tastypie/resources.py
    """

    def detail_uri_kwargs(self, bundle_or_obj):
        """
        Given a ``Bundle`` or an object, it returns the extra kwargs needed
        to generate a detail URI.

        By default, it uses ``_id`` (which is MongoDB's pk) in order to create the URI.
        """

        detail_uri_name = getattr(self._meta, 'detail_uri_name', '_id')
        kwargs = {}

        if isinstance(bundle_or_obj, Bundle):
            if isinstance(bundle_or_obj.obj, ObjectId):
                kwargs[detail_uri_name] = str(bundle_or_obj.obj)
            else:
                kwargs[detail_uri_name] = getattr(bundle_or_obj.obj, detail_uri_name)
        else:
            kwargs[detail_uri_name] = getattr(bundle_or_obj, detail_uri_name)

        return kwargs

    def get_object_list(self, request):
       bundle = self.build_bundle(request=request)
       return self.obj_get_list(bundle)

    def obj_get_list(self, bundle, **kwargs):
        """
        Maps mongodb documents to resource's object class.
        """
        filters     = {}
        obj_list    = []

        # Get filters from query string
        if hasattr(bundle.request, 'GET'):
            # Grab a mutable copy.
            filters = bundle.request.GET.copy()

         # Update with the provided kwargs.
        filters.update(kwargs)

        applicable_filters = self.build_filters(filters=filters)

        obj_list = self.apply_filters(bundle.request, applicable_filters)

        obj_list = self.authorized_read_list(obj_list, bundle)

        return obj_list

    def obj_get(self, bundle, **kwargs):
        """
        Returns mongodb document from provided id.
        """

        obj = self._get_collection().find_one({
            "_id": ObjectId(kwargs.get("_id"))
        })

        if not obj:
            raise ObjectDoesNotExist

        self.authorized_read_detail(obj, bundle)

        return self._get_object_class()(obj)


    def apply_filters(self, request, applicable_filters):
        return list(map(self._get_object_class(), self._get_collection().find(applicable_filters)))

    def build_filters(self, filters):
        applicable_filters = {}
        if isinstance(filters, QueryDict):
            filters = filters.dict()

        for filter_expr, value in filters.items():
            filter_bits = filter_expr.split(LOOKUP_SEP, 1) # We do not support field lookups as data is not ORM-based, so maxsplit=1
            field_name = filter_bits.pop(0)
            filter_type = 'exact'

            if not field_name in self.fields:
                # It's not a field we know about. Move along citizen.
                continue

            if len(filter_bits) and filter_bits[-1] in QUERY_TERMS:
                filter_type = filter_bits.pop()

            if field_name == 'id' or field_name.endswith('_id'):
                # All IDs are represented as strings, but must be converted to ObjectId()
                value = ObjectId(value)

            if filter_type == 'exact':
                applicable_filters[field_name] = value
            elif filter_type in ['gt', 'gte', 'lt', 'lte', 'ne', 'nin', 'in']:
                applicable_filters[field_name] = {
                    "${}".format(filter_type): value
                }
            elif filter_type.endswith('regex'):
                applicable_filters[field_name] = {
                    '$regex':   value
                }
                if filter_type.startswith('i'):
                    applicable_filters[field_name]['$options'] = 'i'

        return applicable_filters

    def _get_object_class(self):
        return self._meta.object_class

    def _get_collection(self):
        """
        Encapsulates collection name.
        """
        try:
            return db[self._meta.collection]
        except Exception as e:
            self.unauthorized_result(e)
