|PyPI Version| |Build Status|

redis-limpyd-extensions
=======================

Some extensions for
`redis-limpyd <https://github.com/yohanboniface/redis-limpyd>`__
(`redis <http://redis.io>`__ orm (sort of) in python)

Where to find it:

-  Github repository: https://github.com/twidi/redis-limpyd-extensions
-  Pypi package: https://pypi.python.org/pypi/redis-limpyd-extensions
-  Documentation: http://documentup.com/twidi/redis-limpyd-extensions

Install:

Python 2.6, 2.7, 3.3 and 3.4 are supported.

.. code:: bash

    pip install redis-limpyd-extensions

List of available extensions:

-  Add/remove related on both sides
-  Dynamic fields

Add/remove related on both sides
--------------------------------

Say we have the following related models:

.. code:: python

        class Person(RelatedModel):
            database = main_database
            name = HashableField(indexable=True)

        class Group(Relatedmodel):
            database = main_database
            name = HashableField(indexable=True)
            members = M2MSetField(Person, related_name='membership')

And some data:

.. code:: python

        somebody = Person(name='foobar')
        group_1 = Group(name='group 1')
        group_2 = Group(name='group 2')
        group_3 = Group(name='group 3')

We can add membership the normal way:

.. code:: python

        group_1.members.sadd(somebody)

And retrieving then this way:

.. code:: python

        group_1_members = group_1.members()  # somebody !
        somebody_membership = somebody.membership()  # group_1

But say that we want to put a person in many groups at ones, we can do:

.. code:: python

        group_2.members.sadd(somebody)
        group_3.members.sadd(somebody)

``limpyd_extensions`` provide a way to add/remove relations via the
other side of the relation:

.. code:: python

        somebody.membership.sadd(group2, group3)

To use this, simple import the related fields from
``limpyd_extensions.related`` instead of ``limpyd.contrib.related``:

.. code:: python

    from limpyd_extensions.related import (FKStringField, FKHashableField, 
                                           M2MSetField, M2MListField, 
                                           M2MSortedSetField)

And use them as usual. (Note that for convenience you can also import
the standard ``RelatedModel`` from there)

The added methods for the reverse side of each related field are:

FKStringField
~~~~~~~~~~~~~

-  ``sadd``, to set the reverse relation as the fk of the arguments:

Having:

.. code:: python

        class Group(RelatedModel):
            parent = FKStringField(self, related_name='children')

The standard:

.. code:: python

        child_group.parent.set(main_group)
        other_child_group.parent.set(main_group)

is the same as the new:

.. code:: python

        main_group.children.sadd(child_group, other_child_group)

-  ``srem`` works the same way as ``sadd`` but for deleting fk:

The standard:

.. code:: python

        child_group.parent.delete(main_group)
        other_child_group.parent.delete(main_group)

is the same as the new:

.. code:: python

        main_group.children.srem(child_group, other_child_group)

FKHashableField
~~~~~~~~~~~~~~~

-  ``sadd``
-  ``srem``

Both work the exact same way as for FKStringField, the only difference
is that ``sadd`` emulates a ``hset``, not a ``set``.

M2MSetField
~~~~~~~~~~~

-  ``sadd``

The standard:

.. code:: python

        group_2.members.sadd(somebody)
        group_3.members.sadd(somebody)

is the same as the new:

.. code:: python

        somebody.membership.sadd(group2, group3)

-  ``srem`` works the same way as ``sadd`` but for removing relations:

The standard:

.. code:: python

        group_2.members.srem(somebody)
        group_3.members.srem(somebody)

is the same as the new:

.. code:: python

        somebody.membership.srem(group2, group3)

M2MListField
~~~~~~~~~~~~

-  ``lpush`` and ``rpush``, that works for ``M2MListField`` like
   ``sadd`` for ``M2MSetField``

If in our Person/Group example ``members`` is a ``M2MListField`` instead
of a ``M2MSetField``,

The standard:

.. code:: python

        group_2.members.rpush(somebody)
        group_3.members.rpush(somebody)

is the same as the new:

.. code:: python

        somebody.membership.rpush(group2, group3)

-  ``lrem`` works the same way as ``rpush`` and ``lpush`` but for
   removing relations:

The standard:

.. code:: python

        group_2.members.lrem(0, somebody)  # 0 for "all occurences"
        group_3.members.lrem(0, somebody)

is the same as the new:

.. code:: python

        somebody.membership.lrem(group2, group3)  # the count is forced to 0

M2MSortedSetField
~~~~~~~~~~~~~~~~~

-  ``zadd`` that works for ``M2MSortedSetField`` like ``sadd`` for
   ``M2MSetField``, but managing scores. Arguments can be set the same
   way as the normal ``zadd`` command.

If in our Person/Group example ``members`` is a ``M2MSortedSetField``
instead of a ``M2MSetField``, using the score to save the date of
membership

The standard:

.. code:: python

        group_2.members.zadd(sometime, somebody)  # sometime, a float, can be a call to time.time()
        group_3.members.zadd(another_time, somebody)

is the same as the new:

.. code:: python

        somebody.membership.zadd(sometime, group2, another_time, group3)

-  ``zrem`` works the same way as ``zadd``, without the score, but for
   removing relations:

The standard:

.. code:: python

        group_2.members.zrem(somebody)
        group_3.members.zrem(somebody)

is the same as the new:

.. code:: python

        somebody.membership.zrem(group2, group3)

Dynamic fields
--------------

Dynamic fields provide a way to add unlimited fields to a model by
defining a (or many) dynamic field, and use it with a dynamic part. ie a
dynamic field name "foo" can be used with as many dynamic parts as you
want to create dynamic variations: "foo\_bar" for the dynamic part
"bar", "foo\_baz" for the dynamic part "baz", and so on.

A simple API to use them, and filter on them, is provided.

To use a dynamic field, your model must inherit from the following
mixin: ``ModelWithDynamicFieldMixin``, found in
``limpyd_extensions.dynamic.model``. It's a mixin, you should use it
with another ``RedisModel`` class. Fields are available as field classes
(``DynamicStringField``, ``DynamicInstanceHashField``,
``DynamicListField``, ``DynamicSetField``, ``DynamicSortedSetField``,
``DynamicHashField``) or as a mixin (``DynamicFieldMixin``) if you want
to adapt an external field. You can find them in
``limpyd_extensions.dynamic.fields``

A short example on how to define a dynamic field on a model:

.. code:: python

    from limpyd.model import RedisModel

    from limpyd_extension.dynamic.model import ModelWithDynamicFieldMixin
    from limpyd_extension.dynamic.fields import DynamicSetField


    class MyModel(ModelWithDynamicFieldMixin, RedisModel):
        foo = DynamicSetField(indexable=True)

As the ``foo`` field is dynamic, you cannot run any command on it, but
only on its dynamic variations. How to do it ?

There is two ways:

-  use the ``get_field`` method of the model:

.. code:: python

    foo_bar = myinstance.get_field('foo_bar')

-  use the ``get_for`` method of the field:

.. code:: python

    foo_bar = myinstance.foo.get_for('bar')

The latter is useful if you have a variable instead of known value:

.. code:: python

    somebar = 'bar'
    foo_bar = myinstance.foo.get_for(somevar)

Note that you can use this shortcut instead of using ``get_for``:

.. code:: python

    foo_bar = myinstance.foo(somevar)

Knowing this, you can do operations on these fields:

::

    myinstance.foo(somevar).sadd('one', 'two', 'three')
    myinstance.foo(othervar).sadd('four', 'five')
    myotherinstance.foo(somevar).sadd('three', 'thirty')
    print myinstance.foo(somevar).smembers()
    print myinstance.foo(othervar).smembers()
    print myotherinstance.foo(somevar).smembers()

To filter on indexable dynamic fields, there is two ways too:

-  use the classic way, if you now the dynamic part in advance:

.. code:: python

    MyModel.collection(foo_bar='three')

-  use the new ``dynamic_filter`` method:

.. code:: python

    MyModel.collection().dynamic_filter('foo', 'bar', 'three')

Parameters are: the field name, the dynamic part, and the value for the
filter.

The collection manager used with ``ModelWithDynamicFieldMixin`` depends
on ``ExtendedCollectionManager``, so you can chain filters and dynamic
filters on the resulting collection.

Dynamic related fields
~~~~~~~~~~~~~~~~~~~~~~

Dynamic fields also work with related fields, exactly the same way.
There is only two additions:

-  if you pass a model instance in the ``get_for`` method, it will be
   translated to it's pk
-  the first argument of a "related collection" is the dynamic part (can
   also be an instance)

An exemple using dynamic related fields:

.. code:: python

    from limpyd.fields import PKField
    from limpyd_extensions.dynamic.model import ModelWithDynamicFieldMixin
    from limpyd_extensions.dynamic.related import DynamicM2MSetField

    class Tag(MyBaseModel):
        slug = PKField()

    class Person(MyBaseModel):
        name = PKField()

    class Movie(ModelWithDynamicFieldMixin, MyBaseModel):
        name = PKField()
        tags = DynamicM2MSetField(Tag, related_name='movies')

    somebody = Person(name='Somebody')
    matrix = Movie(name='Matrix')
    cool = Tag(name='cool')

    matrix.tags.get_for(somebody).sadd(cool)
    # same as: matrix.tags(somebody).sadd(cool)

    cool_movies_for_somebody = cool.movies(somebody)  # the related collection
    # ['Matrix']

Provided classes
~~~~~~~~~~~~~~~~

Here is the list of modules and classes provided with the
``limpyd_extensions.dynamic`` module:

-  **model**

   -  **mixins**

      -  ``ModelWithDynamicFieldMixin(object)`` - A mixin tu use for
         your model with dynamic fields

-  **collection**

   -  **mixins**

      -  ``CollectionManagerForModelWithDynamicFieldMixin(object)`` - A
         mixin to use if you want to add the ``dynamic_filter`` method
         to your own collection manager

   -  **full classes**

      -  ``CollectionManagerForModelWithDynamicField(CollectionManagerForModelWithDynamicFieldMixin, ExtendedCollectionManager)``
         - A simple class inheriting from our mixin and the manager from
         ``limpyd.contrib.collection``

-  **field**

   -  **mixins**

      -  ``DynamicFieldMixin(object)`` - A mixin within all the stuff
         for dynamic fields is done, to use to add dynamic field support
         to your own fields

   -  **full classes** All fields simply inherits from our mixin and the
      wanted base field, without anymore addition:

      -  ``DynamicStringField(DynamicFieldMixin, StringField)``
      -  ``DynamicInstanceHashField(DynamicFieldMixin, InstanceHashField)``
      -  ``DynamicListField(DynamicFieldMixin, ListField)``
      -  ``DynamicSetField(DynamicFieldMixin, SetField)``
      -  ``DynamicSortedSetField(DynamicFieldMixin, SortedSetField)``
      -  ``DynamicHashField(DynamicFieldMixin, HashField)``

-  **related**

   -  **mixins**

      -  ``DynamicRelatedFieldMixin(DynamicFieldMixin)`` - A mixin
         within all the stuff for dynamic related fields is done, to use
         to add dynamic field support to your own related fields

   -  **full classes**

      -  ``DynamicFKStringField(DynamicRelatedFieldMixin, FKStringField)``
      -  ``DynamicFKInstanceHashField(DynamicRelatedFieldMixin, FKInstanceHashField)``
      -  ``DynamicM2MSetField(DynamicRelatedFieldMixin, M2MSetField)``
      -  ``DynamicM2MListField(DynamicRelatedFieldMixin, M2MListField)``
      -  ``DynamicM2MSortedSetField(DynamicRelatedFieldMixin, M2MSortedSetField)``

|Bitdeli Badge|

.. |PyPI Version| image:: https://pypip.in/v/redis-limpyd-extensions/badge.png
   :target: https://pypi.python.org/pypi/redis-limpyd-extensions
.. |Build Status| image:: https://travis-ci.org/twidi/redis-limpyd-extensions.png?branch=master
   :target: https://travis-ci.org/twidi/redis-limpyd-extensions
.. |Bitdeli Badge| image:: https://d2weczhvl823v0.cloudfront.net/twidi/redis-limpyd-extensions/trend.png
   :target: https://bitdeli.com/free
