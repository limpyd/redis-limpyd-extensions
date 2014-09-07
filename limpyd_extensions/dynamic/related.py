# -*- coding:utf-8 -*-
from __future__ import unicode_literals
from future.builtins import object

from limpyd.contrib.related import re_identifier

from ..related import (FKStringField, FKInstanceHashField,
                       M2MSetField, M2MListField, M2MSortedSetField,
                       RelatedCollectionForString, RelatedCollectionForInstanceHash,
                       RelatedCollectionForSet, RelatedCollectionForList, RelatedCollectionForSortedSet)

from .fields import DynamicFieldMixin


class RelatedCollectionMixinForDynamicField(object):

    def __call__(self, dynamic_part, **filters):
        """
        Return a collection on the related model, given the current instance as
        a filter for the related field. Take the dyanmic part of the dynamic
        field to consider as a first argument.
        """
        dynamic_field_name = self.related_field.get_name_for(dynamic_part)

        if not filters:
            filters = {}

        filters[dynamic_field_name] = self.instance._pk

        return self.related_field._model.collection(**filters)


class RelatedCollectionForDynamicString(RelatedCollectionMixinForDynamicField, RelatedCollectionForString):
    pass


class RelatedCollectionForDynamicInstanceHash(RelatedCollectionMixinForDynamicField, RelatedCollectionForInstanceHash):
    pass


class RelatedCollectionForDynamicSet(RelatedCollectionMixinForDynamicField, RelatedCollectionForSet):
    pass


class RelatedCollectionForDynamicList(RelatedCollectionMixinForDynamicField, RelatedCollectionForList):
    pass


class RelatedCollectionForDynamicSortedSet(RelatedCollectionMixinForDynamicField, RelatedCollectionForSortedSet):
    pass


class DynamicRelatedFieldMixin(DynamicFieldMixin):
    """
    As the related name must be unique for a relation between two objects, we
    have to make a fake one for this dynamic field, based on its dynamic name.
    """
    def _get_related_name(self):
        if self.dynamic_version_of is not None:
            self.related_name = '%s__%s__%s' % (
                self.dynamic_version_of.related_name,
                re_identifier.sub('_', self.dynamic_part),
                id(self)
            )
        return super(DynamicRelatedFieldMixin, self)._get_related_name()

    def get_name_for(self, dynamic_part):
        """
        Return the name for the current dynamic field, accepting a limpyd
        instance for the dynamic part
        """
        dynamic_part = self.from_python(dynamic_part)
        return super(DynamicRelatedFieldMixin, self).get_name_for(dynamic_part)


class DynamicFKStringField(DynamicRelatedFieldMixin, FKStringField):
    related_collection_class = RelatedCollectionForDynamicString


class DynamicFKInstanceHashField(DynamicRelatedFieldMixin, FKInstanceHashField):
    related_collection_class = RelatedCollectionForDynamicInstanceHash


class DynamicM2MSetField(DynamicRelatedFieldMixin, M2MSetField):
    related_collection_class = RelatedCollectionForDynamicSet


class DynamicM2MListField(DynamicRelatedFieldMixin, M2MListField):
    related_collection_class = RelatedCollectionForDynamicList


class DynamicM2MSortedSetField(DynamicRelatedFieldMixin, M2MSortedSetField):
    related_collection_class = RelatedCollectionForDynamicSortedSet
