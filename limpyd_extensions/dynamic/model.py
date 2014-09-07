# -*- coding:utf-8 -*-
from __future__ import unicode_literals
from future.builtins import object


from limpyd import fields as limpyd_fields

from .collection import CollectionManagerForModelWithDynamicField


class ModelWithDynamicFieldMixin(object):
    """
    This mixin must be used to declare each model that is intended to use a
    DynamicField, creating fields on the fly when needed.
    """

    _dynamic_fields_cache = {}
    collection_manager = CollectionManagerForModelWithDynamicField

    @classmethod
    def _get_dynamic_field_for(cls, field_name):
        """
        Return the dynamic field within this class that match the given name.
        Keep an internal cache to speed up future calls wieh same field name.
        (The cache store the field for each individual class and subclasses, to
        keep the link between a field and its direct model)
        """
        from .fields import DynamicFieldMixin  # here to avoid circular import

        if cls not in ModelWithDynamicFieldMixin._dynamic_fields_cache:
            ModelWithDynamicFieldMixin._dynamic_fields_cache[cls] = {}

        if field_name not in ModelWithDynamicFieldMixin._dynamic_fields_cache[cls]:
            ModelWithDynamicFieldMixin._dynamic_fields_cache[cls][field_name] = None
            for a_field_name in cls._fields:
                field = cls.get_field(a_field_name)
                if isinstance(field, DynamicFieldMixin) and field._accept_name(field_name):
                    ModelWithDynamicFieldMixin._dynamic_fields_cache[cls][field_name] = field
                    break

        field = ModelWithDynamicFieldMixin._dynamic_fields_cache[cls][field_name]

        if field is None:
            raise ValueError('No DynamicField matching "%s"' % field_name)

        return field

    @classmethod
    def has_field(cls, field_name):
        """
        Check if the current class has a field with the name "field_name"
        Add management of dynamic fields, to return True if the name matches an
        existing dynamic field without existing copy for this name.
        """
        if super(ModelWithDynamicFieldMixin, cls).has_field(field_name):
            return True

        try:
            cls._get_dynamic_field_for(field_name)
        except ValueError:
            return False
        else:
            return True

    @classmethod
    def get_class_field(cls, field_name):
        """
        Add management of dynamic fields: if a normal field cannot be retrieved,
        check if it can be a dynamic field and in this case, create a copy with
        the given name and associate it to the model.
        """
        try:
            field = super(ModelWithDynamicFieldMixin, cls).get_class_field(field_name)
        except AttributeError:
            # the "has_field" returned True but getattr raised... we have a DynamicField
            dynamic_field = cls._get_dynamic_field_for(field_name)
            field = cls._add_dynamic_field_to_model(dynamic_field, field_name)

        return field

    # at the class level, we use get_class_field to get a field
    # but in __init__, we update it to use get_instance_field
    get_field = get_class_field

    def get_instance_field(self, field_name):
        """
        Add management of dynamic fields: if a normal field cannot be retrieved,
        check if it can be a dynamic field and in this case, create a copy with
        the given name and associate it to the instance.
        """
        try:
            field = super(ModelWithDynamicFieldMixin, self).get_instance_field(field_name)
        except AttributeError:
            # the "has_field" returned True but getattr raised... we have a DynamicField
            dynamic_field = self._get_dynamic_field_for(field_name)  # it's a model bound field
            dynamic_field = self.get_field(dynamic_field.name)  # we now have an instance bound field
            field = self._add_dynamic_field_to_instance(dynamic_field, field_name)

        return field

    @classmethod
    def _add_dynamic_field_to_model(cls, field, field_name):
        """
        Add a copy of the DynamicField "field" to the current class and its
        subclasses using the "field_name" name
        """
        # create the new field
        new_field = field._create_dynamic_version()
        new_field.name = field_name
        new_field._attach_to_model(cls)

        # set it as an attribute on the class, to be reachable
        setattr(cls, "_redis_attr_%s" % field_name, new_field)

        # NOTE: don't add the field to the "_fields" list, to avoid use extra
        #       memory to each future instance that will create a field for each
        #       dynamic one created

        # # add the field to the list to avoid to done all of this again
        # # (_fields is already on this class only, not subclasses)
        # cls._fields.append(field_name)

        # each subclass needs its own copy
        for subclass in cls.__subclasses__():
            subclass._add_dynamic_field_to_model(field, field_name)

        return new_field

    def _add_dynamic_field_to_instance(self, field, field_name):
        """
        Add a copy of the DynamicField "field" to the current instance using the
        "field_name" name
        """
        # create the new field
        new_field = field._create_dynamic_version()
        new_field.name = field_name
        new_field._attach_to_instance(self)

        # add the field to the list to avoid doing all of this again
        if field_name not in self._fields:  # (maybe already in it via the class)
            if id(self._fields) == id(self.__class__._fields):
                # unlink the list from the class
                self._fields = list(self._fields)
            self._fields.append(field_name)

        # if the field is an hashable field, add it to the list to allow calling
        # hmget on these fields
        if isinstance(field, limpyd_fields.InstanceHashField):
            if id(self._instancehash_fields) == id(self.__class__._instancehash_fields):
                # unlink the link from the class
                self._instancehash_fields = list(self._instancehash_fields)
            self._instancehash_fields.append(field_name)

        # set it as an attribute on the instance, to be reachable
        setattr(self, field_name, new_field)

        return new_field

    @classmethod
    def get_field_name_for(cls, field_name, dynamic_part):
        """
        Given the name of a dynamic field, and a dynamic part, return the
        name of the final dynamic field to use. It will then be used with
        get_field.
        """
        field = cls.get_field(field_name)
        return field.get_name_for(dynamic_part)
