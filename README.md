redis-limpyd-extensions
=======================

Some extensions for [redis-limpyd][] ([redis][] orm (sort of) in python)

Github repository: <https://github.com/twidi/redis-limpyd-extensions>

Note that you actually need the [develop branch of the twidi's fork of redis-limpyd][twidi-limpyd]

List of available extensions:

* [Add/remove related on both sides] (#addremove-related-on-both-sides)


## Add/remove related on both sides ##

Say we have the following models:

```python
    class Person(RelatedModel):
        database = main_database
        name = HashableField(indexable=True)

    class Group(Relatedmodel):
        database = main_database
        name = HashableField(indexable=True)
        members = M2MSetField(Person, related_name='membership')
```

And some data:

```python
    somebody = Person(name='foobar')
    group_1 = Person(name='group 1')
    group_2 = Person(name='group 2')
    group_3 = Person(name='group 3')
```

We can add membership the normal way:

```python
    group1.members.sadd(somebody)
```

And retrieving then this way:

```python
    group_1_members = group_1.members()  # somebody !
    somebody_membership = somebody.membership()  # group_1
```

But say that we want to put a person in many groups at ones, we can do:

```python
    group_2.members.sadd(somebody)
    group_3.members.sadd(somebody)
```

`limpyd_extensions` provide a way to add/remove relations via the other side of
the relation:

```python
    somebody.membership.sadd(group2, group3)
```

To use this, simple import the related fields from `limpyd_extensions.related` instead of `limpyd.contrib.related`:

```python
from limpyd_extensions.related import (FKStringField, FKHashableField, 
                                       M2MSetField, M2MListField, 
                                       M2MSortedSetField)
```

And use them as usual. (Note that for convenience you can also import the standard `RelatedModel` from there)

The added methods for the reverse side of each related field are:

### FKStringField ###

* `sadd`, to set the reverse relation as the fk of the arguments:

Having:

```python
    class Group(RelatedModel):
        parent = FKStringField(self, related_name='children')
```

The standard:

```python
    child_group.parent.set(main_group)
    other_child_group.parent.set(main_group)
```

is the same as the new:

```python
    main_group.children.sadd(child_group, other_child_group)
```

* `srem` works the same way as `sadd` but for deleting fk:

The standard:

```python
    child_group.parent.delete(main_group)
    other_child_group.parent.delete(main_group)
```

is the same as the new:

```python
    main_group.children.srem(child_group, other_child_group)
```


### FKHashableField ###

* `sadd`
* `srem`

Both work the exact same way as for FKStringField, the only difference is that `sadd` emulates a `hset`, not a `set`.


### M2MSetField ###

* `sadd`

The standard:

```python
    group_2.members.sadd(somebody)
    group_3.members.sadd(somebody)
```

is the same as the new:

```python
    somebody.membership.sadd(group2, group3)
```

* `srem` works the same way as `sadd` but for removing relations:

The standard:

```python
    group_2.members.srem(somebody)
    group_3.members.srem(somebody)
```

is the same as the new:

```python
    somebody.membership.srem(group2, group3)
```


### M2MListField ###

* `lpush` and `rpush`, that works for `M2MListField` like `sadd` for `M2MSetField`

If in our Person/Group example `members` is a `M2MListField` instead of a `M2MSetField`, 

The standard:

```python
    group_2.members.rpush(somebody)
    group_3.members.rpush(somebody)
```

is the same as the new:

```python
    somebody.membership.rpush(group2, group3)
```

* `lrem` works the same way as `rpush` and `lpush` but for removing relations:

The standard:

```python
    group_2.members.lrem(0, somebody)  # 0 for "all occurences"
    group_3.members.lrem(0, somebody)
```

is the same as the new:

```python
    somebody.membership.lrem(group2, group3)  # the count is forced to 0
```


### M2MSortedSetField ###

* `zadd` that works for `M2MSortedSetField` like `sadd` for `M2MSetField`, but managing scores. Arguments can be set the same way as the normal `zadd` command.

If in our Person/Group example `members` is a `M2MSortedSetField` instead of a `M2MSetField`, using the score to save the date of membership


The standard:

```python
    group_2.members.zadd(sometime, somebody)  # sometime, a float, can be a call to time.time()
    group_3.members.zadd(another_time, somebody)
```

is the same as the new:

```python
    somebody.membership.zadd(sometime, group2, another_time, group3)
```

* `zrem` works the same way as `zadd`, without the score, but for removing relations:

The standard:

```python
    group_2.members.zrem(somebody)
    group_3.members.zrem(somebody)
```

is the same as the new:

```python
    somebody.membership.zrem(group2, group3)
```



[redis-limpyd-extensions]: https://github.com/twidi/redis-limpyd-extensions
[redis]: http://redis.io
[redis-limpyd]: https://github.com/yohanboniface/redis-limpyd
[twidi-limpyd]: https://github.com/twidi/redis-limpyd/tree/develop
