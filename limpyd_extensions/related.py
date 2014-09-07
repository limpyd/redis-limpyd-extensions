# -*- coding:utf-8 -*-
from __future__ import unicode_literals
from future.builtins import zip



from limpyd import model, fields
# RelatedModel imported to let users import limpyd_extensions.related with
# all stuff existing or redefined from limpyd.contrib.related
from limpyd.contrib.related import (RelatedCollection, RelatedModel,
                                    FKStringField as BaseFKStringField,
                                    FKInstanceHashField as BaseFKInstanceHashField,
                                    M2MSetField as BaseM2MSetField,
                                    M2MListField as BaseM2MListField,
                                    M2MSortedSetField as BaseM2MSortedSetFiel)


class _RelatedCollectionWithMethods(RelatedCollection):

    def _to_fields(self, *values):
        """
        Take a list of values, which must be primary keys of the model linked
        to the related collection, and return a list of related fields.
        """
        result = []
        for related_instance in values:
            if not isinstance(related_instance, model.RedisModel):
                related_instance = self.related_field._model(related_instance)
            result.append(getattr(related_instance, self.related_field.name))
        return result

    def _reverse_call(self, related_method, *values):
        """
        Convert each value to a related field, then call the method on each
        field, passing self.instance as argument.
        If related_method is a string, it will be the method of the related field.
        If it's a callable, it's a function which accept the related field and
        self.instance.
        """
        related_fields = self._to_fields(*values)
        for related_field in related_fields:
            if callable(related_method):
                related_method(related_field, self.instance._pk)
            else:
                getattr(related_field, related_method)(self.instance._pk)


class _RelatedCollectionForFK(_RelatedCollectionWithMethods):
    _set_method = None

    def sadd(self, *values):
        """
        Do a "hset/set" call with self.instance as parameter for each value. Values
        must be primary keys of the related model.
        """
        self._reverse_call(self._set_method, *values)

    def srem(self, *values):
        """
        Do a "set" call with self.instance as parameter for each value. Values
        must be primary keys of the related model.
        """
        self._reverse_call(lambda related_field, value: related_field.delete(), *values)


class RelatedCollectionForString(_RelatedCollectionForFK):
    """
    A RelatedCollection for FKStringField that can simulate calls to a real Set.
    Available methods: sadd and srem.
    """
    _set_method = 'set'


class RelatedCollectionForInstanceHash(_RelatedCollectionForFK):
    """
    A RelatedCollection for FKInstanceHashField that can simulate calls to a real Set.
    Available methods: sadd and srem.
    """
    _set_method = 'hset'


class RelatedCollectionForSet(_RelatedCollectionWithMethods):
    """
    A RelatedCollection for M2MSetField that can simulate calls to a real Set
    Available methods: sadd and srem.
    """

    def sadd(self, *values):
        """
        Do a "sadd" call with self.instance as parameter for each value. Values
        must be primary keys of the related model.
        """
        self._reverse_call('sadd', *values)

    def srem(self, *values):
        """
        Do a "srem" call with self.instance as parameter for each value. Values
        must be primary keys of the related model.
        """
        self._reverse_call('srem', *values)


class RelatedCollectionForList(_RelatedCollectionWithMethods):
    """
    A RelatedCollection for M2MListField that can simulate calls to a real List.
    Available methods: lpush, rpush and lrem.
    """

    def lpush(self, *values):
        """
        Do a "lpush" call with self.instance as parameter for each value. Values
        must be primary keys of the related model.
        """
        self._reverse_call('lpush', *values)

    def rpush(self, *values):
        """
        Do a "rpush" call with self.instance as parameter for each value. Values
        must be primary keys of the related model.
        """
        self._reverse_call('rpush', *values)

    def lrem(self, *values):
        """
        Do a "lrem" call with self.instance as parameter for each value. Values
        must be primary keys of the related model.
        The "count" argument of the final call will be 0 to remove all the
        matching values.
        """
        self._reverse_call(lambda related_field, value: related_field.lrem(0, value), *values)


class RelatedCollectionForSortedSet(_RelatedCollectionWithMethods):
    """
    A RelatedCollection for M2MSortedSetField that can simulate calls to a real
    SortedSet
    Available methods: zadd and zrem
    """

    def zadd(self, *args, **kwargs):
        """
        For each score/value given as paramter, do a "zadd" call with
        score/self.instance as parameter call for each value. Values must be
        primary keys of the related model.
        """
        if 'values_callback' not in kwargs:
            kwargs['values_callback'] = self._to_fields
        pieces = fields.SortedSetField.coerce_zadd_args(*args, **kwargs)
        for (score, related_field) in zip(*[iter(pieces)] * 2):
            related_method = getattr(related_field, 'zadd')
            related_method(score, self.instance._pk, values_callback=None)

    def zrem(self, *values):
        """
        Do a "zrem" call with self.instance as parameter for each value. Values must
        must be primary keys of the related model.
        """
        self._reverse_call('zrem', *values)


class FKStringField(BaseFKStringField):
    related_collection_class = RelatedCollectionForString


class FKInstanceHashField(BaseFKInstanceHashField):
    related_collection_class = RelatedCollectionForInstanceHash


class M2MSetField(BaseM2MSetField):
    related_collection_class = RelatedCollectionForSet


class M2MListField(BaseM2MListField):
    related_collection_class = RelatedCollectionForList


class M2MSortedSetField(BaseM2MSortedSetFiel):
    related_collection_class = RelatedCollectionForSortedSet
