# -*- coding:utf-8 -*-
from __future__ import unicode_literals
from future.builtins import object

from copy import copy
import re

from limpyd import fields as limpyd_fields
from limpyd.exceptions import ImplementationError

from .model import ModelWithDynamicFieldMixin


class DynamicFieldMixin(object):
    """
    This mixin adds a main functionnality to each domain it's attached to: the
    ability to have an unlimited number of fields. If a field is asked in the
    model which not exists, it will ask to each of its dynamic fields if it
    can accepts the wanted field name. If True, a new field is created on the
    fly with this new name.
    The matching is done using the "pattern" argument to pass when declaring
    the dynamic field on the model. This argument must be a regular expression
    (or a string, but in both cases the "re.compile" method will be called).
    If not defined, the default pattern will be used: ^basefieldname_\d+$ (here,
    basefieldname is the name used to declare the field on the model)
    To to the reverse operation, ie get a field name based on a dynamic part,
    the "format" argument can be passed when declaring the dynamic field on the
    model. Both pattern and format must match. If not defined, the default
    format is 'basefieldname_%s'.
    """

    def __init__(self, *args, **kwargs):
        """
        Handle the new optional "pattern" attribute
        """
        self._pattern = kwargs.pop('pattern', None)
        if self._pattern:
            self._pattern = re.compile(self._pattern)

        self._format = kwargs.pop('format', None)

        self.dynamic_version_of = None

        super(DynamicFieldMixin, self).__init__(*args, **kwargs)

    def _attach_to_model(self, model):
        """
        Check that the model can handle dynamic fields
        """
        if not issubclass(model, ModelWithDynamicFieldMixin):
            raise ImplementationError(
                'The "%s" model does not inherit from ModelWithDynamicFieldMixin '
                'so the "%s" DynamicField cannot be attached to it' % (
                model.__name__, self.name))

        super(DynamicFieldMixin, self)._attach_to_model(model)

        if self.dynamic_version_of is not None:
            return

        if hasattr(model, self.name):
            return

        setattr(model, self.name, self)

    @property
    def pattern(self):
        """
        Return the pattern used to check if a field name can be accepted by this
        dynamic field. Use a default one ('^fieldname_(.+)$') if not set when
        the field was initialized
        """
        if self.dynamic_version_of is not None:
            return self.dynamic_version_of.pattern

        if not self._pattern:
            self._pattern = re.compile('^%s_(.+)$' % self.name)
        return self._pattern

    @property
    def format(self):
        """
        Return the format used to create the name of a variation of the current
        dynamic field. Use a default one ('fieldname_%s') if not set when the
        field was initialized
        """
        if self.dynamic_version_of is not None:
            return self.dynamic_version_of.format

        if not self._format:
            self._format = '%s_%%s' % self.name
        return self._format

    @property
    def dynamic_part(self):
        if not hasattr(self, '_dynamic_part'):
            self._dynamic_part = self.pattern.match(self.name).groups()[0]
        return self._dynamic_part

    def _accept_name(self, field_name):
        """
        Return True if the given field name can be accepted by this dynamic field
        """
        return bool(self.pattern.match(field_name))

    def __copy__(self):
        """
        Copy the _pattern attribute to the new copy of this field
        """
        new_copy = super(DynamicFieldMixin, self).__copy__()
        new_copy._pattern = self._pattern
        return new_copy

    def _create_dynamic_version(self):
        """
        Create a copy of the field and set it as a dynamic version of it.
        """
        new_field = copy(self)
        new_field.dynamic_version_of = self
        return new_field

    def _base_field(self):
        """
        Return the base field (the one without variable part) of the current one.
        """
        return self.dynamic_version_of or self

    @property
    def _inventory(self):
        """
        Return (and create if needed) the internal inventory field, a SetField
        used to track all dynamic versions used on a specific instance.
        """
        if self.dynamic_version_of:
            return self.dynamic_version_of._inventory

        if not hasattr(self, '_inventory_field'):
            self._inventory_field = limpyd_fields.SetField()
            self._inventory_field._attach_to_model(self._model)
            self._inventory_field._attach_to_instance(self._instance)
            self._inventory_field.lockable = True
            self._inventory.name = self.name

        return self._inventory_field

    def _call_command(self, name, *args, **kwargs):
        """
        If a command is called for the main field, without dynamic part, an
        ImplementationError is raised: commands can only be applied on dynamic
        versions.
        On dynamic versions, if the command is a modifier, we add the version in
        the inventory.
        """
        if self.dynamic_version_of is None:
            raise ImplementationError('The main version of a dynamic field cannot accept commands')
        try:
            result = super(DynamicFieldMixin, self)._call_command(name, *args, **kwargs)
        except:
            raise
        else:
            if name in self.available_modifiers and name not in ('delete', 'hdel'):
                self._inventory.sadd(self.dynamic_part)
            return result

    def delete(self):
        """
        If a dynamic version, delete it the standard way and remove it from the
        inventory, else delete all dynamic versions.
        """
        if self.dynamic_version_of is None:
            self._delete_dynamic_versions()
        else:
            super(DynamicFieldMixin, self).delete()
            self._inventory.srem(self.dynamic_part)

    def _delete_dynamic_versions(self):
        """
        Call the `delete` method of all dynamic versions of the current field
        found in the inventory then clean the inventory.
        """
        if self.dynamic_version_of:
            raise ImplementationError(u'"_delete_dynamic_versions" can only be '
                                      u'executed on the base field')
        inventory = self._inventory
        for dynamic_part in inventory.smembers():
            name = self.get_name_for(dynamic_part)
            # create the field
            new_field = self._create_dynamic_version()
            new_field.name = name
            new_field._dynamic_part = dynamic_part  # avoid useless computation
            new_field._attach_to_model(self._model)
            new_field._attach_to_instance(self._instance)
            # and delete its content
            new_field.delete()

        inventory.delete()

    def get_name_for(self, dynamic_part):
        """
        Compute the name of the variation of the current dynamic field based on
        the given dynamic part. Use the "format" attribute to create the final
        name.
        """
        name = self.format % dynamic_part
        if not self._accept_name(name):
            raise ImplementationError('It seems that pattern and format do not '
                                      'match for the field "%s"' % self.name)
        return name

    def get_for(self, dynamic_part):
        """
        Return a variation of the current dynamic field based on the given
        dynamic part. Use the "format" attribute to create the final name
        """
        if not hasattr(self, '_instance'):
            raise ImplementationError('"get_for" can be used only on a bound field')
        name = self.get_name_for(dynamic_part)
        return self._instance.get_field(name)
    __call__ = get_for


class DynamicStringField(DynamicFieldMixin, limpyd_fields.StringField):
    pass


class DynamicInstanceHashField(DynamicFieldMixin, limpyd_fields.InstanceHashField):
    pass


class DynamicListField(DynamicFieldMixin, limpyd_fields.ListField):
    pass


class DynamicSetField(DynamicFieldMixin, limpyd_fields.SetField):
    pass


class DynamicSortedSetField(DynamicFieldMixin, limpyd_fields.SortedSetField):
    pass


class DynamicHashField(DynamicFieldMixin, limpyd_fields.HashField):
    pass
