# -*- coding:utf-8 -*-

from limpyd.contrib.collection import ExtendedCollectionManager


class CollectionManagerForModelWithDynamicFieldMixin(object):
    def dynamic_filter(self, field_name, dynamic_part, value):
        """
        Add a filter to the collection, using a dynamic field. The key part of
        the filter is composed using the field_name, which must be the field
        name of a dynamic field on the attached model, and a dynamic part.
        Finally return the collection, by calling self.filter
        """
        dynamic_field_name = self.cls.get_field(field_name).get_name_for(dynamic_part)
        return self.filter(**{dynamic_field_name: value})


class CollectionManagerForModelWithDynamicField(CollectionManagerForModelWithDynamicFieldMixin, ExtendedCollectionManager):
    """
    A colleciton manager based on ExtendedCollectionManager that add the
    "dynamic_filter" method.
    """
    pass
