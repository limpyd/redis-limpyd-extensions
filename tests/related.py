# -*- coding:utf-8 -*-

import time

from limpyd import fields
from limpyd_extensions import related

from .base import LimpydBaseTest


class TestRedisModel(related.RelatedModel):
    """
    Use it as a base for all RelatedModel created for tests
    """
    database = LimpydBaseTest.database
    abstract = True
    namespace = "related-tests"


class Person(TestRedisModel):
    name = fields.PKField()
    prefered_group = related.FKStringField('Group', related_name='prefered_for')


class Group(TestRedisModel):
    name = fields.PKField()
    parent = related.FKInstanceHashField('self', related_name='children')
    members = related.M2MSetField(Person, related_name='membership')
    lmembers = related.M2MListField(Person, related_name='lmembership')
    zmembers = related.M2MSortedSetField(Person, related_name='zmembership')


class ReverseMethodsTest(LimpydBaseTest):
    def setUp(self):
        super(ReverseMethodsTest, self).setUp()
        self.main_group = Group(name='limpyd groups')
        self.core_devs = Group(name='limpyd core devs')
        self.fan_boys = Group(name='limpyd fan boys')
        self.ybon = Person(name='ybon')
        self.twidi = Person(name='twidi')

    def test_fkstringfield(self):
        # set the legacy way
        self.twidi.prefered_group.set(self.core_devs)
        self.assertEqual(self.twidi.prefered_group.get(), self.core_devs._pk)
        self.assertEqual(set(self.core_devs.prefered_for()), set([self.twidi._pk]))

        # set with the new reversed way
        self.fan_boys.prefered_for.sadd(self.twidi)
        self.assertEqual(self.twidi.prefered_group.get(), self.fan_boys._pk)
        self.assertEqual(set(self.core_devs.prefered_for()), set())
        self.assertEqual(set(self.fan_boys.prefered_for()), set([self.twidi._pk]))

        # remove with the new reversed way
        self.fan_boys.prefered_for.srem(self.twidi)
        self.assertEqual(self.twidi.prefered_group.get(), None)
        self.assertEqual(set(self.fan_boys.prefered_for()), set())

        # set many
        self.core_devs.prefered_for.sadd(self.twidi, self.ybon)
        self.assertEqual(self.twidi.prefered_group.get(), self.core_devs._pk)
        self.assertEqual(self.ybon.prefered_group.get(), self.core_devs._pk)
        self.assertEqual(set(self.core_devs.prefered_for()), set([self.twidi._pk, self.ybon._pk]))

        # remove many
        self.core_devs.prefered_for.srem(self.twidi, self.ybon)
        self.assertEqual(self.twidi.prefered_group.get(), None)
        self.assertEqual(self.ybon.prefered_group.get(), None)
        self.assertEqual(set(self.core_devs.prefered_for()), set())

    def test_fkinstancehashfield(self):
        # set the legacy way
        self.fan_boys.parent.hset(self.main_group)
        self.assertEqual(self.fan_boys.parent.hget(), self.main_group._pk)
        self.assertEqual(set(self.main_group.children()), set([self.fan_boys._pk]))

        # set with the new reversed way
        self.core_devs.children.sadd(self.fan_boys)
        self.assertEqual(self.fan_boys.parent.hget(), self.core_devs._pk)
        self.assertEqual(set(self.main_group.children()), set())
        self.assertEqual(set(self.core_devs.children()), set([self.fan_boys._pk]))

        # remove with the new reversed way
        self.core_devs.children.srem(self.fan_boys)
        self.assertEqual(self.fan_boys.parent.hget(), None)
        self.assertEqual(set(self.core_devs.children()), set())

        # set many
        self.main_group.children.sadd(self.core_devs, self.fan_boys)
        self.assertEqual(self.core_devs.parent.hget(), self.main_group._pk)
        self.assertEqual(self.fan_boys.parent.hget(), self.main_group._pk)
        self.assertEqual(set(self.main_group.children()), set([self.core_devs._pk, self.fan_boys._pk]))

        # remove many
        self.main_group.children.srem(self.core_devs, self.fan_boys)
        self.assertEqual(self.core_devs.parent.hget(), None)
        self.assertEqual(self.fan_boys.parent.hget(), None)
        self.assertEqual(set(self.main_group.children()), set())

    def test_m2msetfield(self):
        # add with the legacy way
        self.core_devs.members.sadd(self.ybon)
        self.assertEqual(set(self.core_devs.members()), set([self.ybon._pk]))
        self.assertEqual(set(self.ybon.membership()), set([self.core_devs._pk]))

        # add with the new reversed way
        self.twidi.membership.sadd(self.core_devs)
        self.assertEqual(set(self.core_devs.members()), set([self.ybon._pk, self.twidi._pk]))
        self.assertEqual(set(self.twidi.membership()), set([self.core_devs._pk]))

        # remove the legacy way
        self.core_devs.members.srem(self.ybon)
        self.assertEqual(set(self.core_devs.members()), set([self.twidi._pk]))
        self.assertEqual(set(self.ybon.membership()), set())

        # remove with the new reversed way
        self.twidi.membership.srem(self.core_devs)
        self.assertEqual(set(self.core_devs.members()), set())
        self.assertEqual(set(self.twidi.membership()), set())

        # add many
        self.twidi.membership.sadd(self.core_devs, self.fan_boys)
        self.assertEqual(set(self.core_devs.members()), set([self.twidi._pk]))
        self.assertEqual(set(self.fan_boys.members()), set([self.twidi._pk]))
        self.assertEqual(set(self.twidi.membership()), set([self.core_devs._pk, self.fan_boys._pk]))

        # remove many
        self.twidi.membership.srem(self.core_devs, self.fan_boys)
        self.assertEqual(set(self.core_devs.members()), set())
        self.assertEqual(set(self.fan_boys.members()), set())
        self.assertEqual(set(self.twidi.membership()), set())

    def test_m2mlistfield(self):
        # add with the legacy way
        self.core_devs.lmembers.rpush(self.ybon)
        self.assertEqual(list(self.core_devs.lmembers()), [self.ybon._pk])
        self.assertEqual(set(self.ybon.lmembership()), set([self.core_devs._pk]))

        # add with the new reversed way
        self.twidi.lmembership.rpush(self.core_devs)
        self.assertEqual(set(self.core_devs.lmembers()), set([self.ybon._pk, self.twidi._pk]))
        self.assertEqual(set(self.twidi.lmembership()), set([self.core_devs._pk]))

        # remove the legacy way
        self.core_devs.lmembers.lrem(0, self.ybon)
        self.assertEqual(set(self.core_devs.lmembers()), set([self.twidi._pk]))
        self.assertEqual(set(self.ybon.lmembership()), set())

        # remove with the new reversed way
        self.twidi.lmembership.lrem(self.core_devs)
        self.assertEqual(set(self.core_devs.lmembers()), set())
        self.assertEqual(set(self.twidi.lmembership()), set())

        # add many
        self.twidi.lmembership.rpush(self.core_devs, self.fan_boys)
        self.assertEqual(set(self.core_devs.lmembers()), set([self.twidi._pk]))
        self.assertEqual(set(self.fan_boys.lmembers()), set([self.twidi._pk]))
        self.assertEqual(set(self.twidi.lmembership()), set([self.core_devs._pk, self.fan_boys._pk]))

        # remove many
        self.twidi.lmembership.lrem(self.core_devs, self.fan_boys)
        self.assertEqual(set(self.core_devs.lmembers()), set())
        self.assertEqual(set(self.fan_boys.lmembers()), set())
        self.assertEqual(set(self.twidi.lmembership()), set())

    def test_m2msortedsetfield(self):
        t2 = time.time()
        t1 = t2 - 100

        # add with the legacy way
        self.core_devs.zmembers.zadd(t1, self.ybon)
        self.assertEqual(set(self.core_devs.zmembers()), set([self.ybon._pk]))
        self.assertEqual(set(self.ybon.zmembership()), set([self.core_devs._pk]))

        # add with the new reversed way
        self.twidi.zmembership.zadd(t2, self.core_devs)
        self.assertEqual(set(self.core_devs.zmembers()), set([self.ybon._pk, self.twidi._pk]))
        self.assertEqual(set(self.twidi.zmembership()), set([self.core_devs._pk]))

        # remove the legacy way
        self.core_devs.zmembers.zrem(self.ybon)
        self.assertEqual(set(self.core_devs.zmembers()), set([self.twidi._pk]))
        self.assertEqual(set(self.ybon.zmembership()), set())

        # remove with the new reversed way
        self.twidi.zmembership.zrem(self.core_devs)
        self.assertEqual(set(self.core_devs.zmembers()), set())
        self.assertEqual(set(self.twidi.zmembership()), set())

        # add many
        self.twidi.zmembership.zadd(t1, self.core_devs, t2, self.fan_boys)
        self.assertEqual(set(self.core_devs.zmembers()), set([self.twidi._pk]))
        self.assertEqual(set(self.fan_boys.zmembers()), set([self.twidi._pk]))
        self.assertEqual(set(self.twidi.zmembership()), set([self.core_devs._pk, self.fan_boys._pk]))

        # remove many
        self.twidi.zmembership.zrem(self.core_devs, self.fan_boys)
        self.assertEqual(set(self.core_devs.zmembers()), set())
        self.assertEqual(set(self.fan_boys.zmembers()), set())
        self.assertEqual(set(self.twidi.zmembership()), set())
