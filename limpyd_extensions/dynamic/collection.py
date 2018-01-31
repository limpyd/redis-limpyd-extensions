# -*- coding:utf-8 -*-
from __future__ import unicode_literals
from future.builtins import object

from limpyd.contrib.collection import ExtendedCollectionManager


class CollectionManagerForModelWithDynamicFieldMixin(object):
    def dynamic_filter(self, field_name, dynamic_part, value, index_suffix=''):
        """
        Add a filter to the collection, using a dynamic field. The key part of
        the filter is composed using the field_name, which must be the field
        name of a dynamic field on the attached model, and a dynamic part.
        The index_suffix allow to specify which index to use. It's an empty string
        by default for the default equal index (could be "__eq" or "eq" to have the
        exact same result)
        Finally return the collection, by calling self.filter
        """
        field_name_parts = field_name.split('__')
        real_field_name = field_name_parts.pop(0)
        dynamic_field_name = self.cls.get_field(real_field_name).get_name_for(dynamic_part)
        field_name_parts.insert(0, dynamic_field_name)
        filter_name = '__'.join(field_name_parts)
        if not index_suffix:
            index_suffix = ''
        elif not index_suffix.startswith('__'):
            index_suffix = '__' + index_suffix
        return self.filter(**{filter_name + index_suffix: value})


class CollectionManagerForModelWithDynamicField(CollectionManagerForModelWithDynamicFieldMixin, ExtendedCollectionManager):
    """
    A colleciton manager based on ExtendedCollectionManager that add the
    "dynamic_filter" method.
    """
    pass
