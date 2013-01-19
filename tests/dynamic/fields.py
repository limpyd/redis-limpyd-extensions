# -*- coding:utf-8 -*-


from limpyd.model import RedisModel
from limpyd import fields as limpyd_fields
from limpyd.exceptions import ImplementationError

from limpyd_extensions.dynamic import fields

from ..base import LimpydBaseTest


class TestRedisModel(RedisModel):
    """
    Use it as a base for all models created for tests
    """
    database = LimpydBaseTest.database
    abstract = True
    namespace = "fields-tests"


class TestRedisModelWithDynamicField(fields.ModelWithDynamicFieldMixin, TestRedisModel):
    abstract = True


class Person(TestRedisModel):
    name = limpyd_fields.PKField()


class Movie(TestRedisModelWithDynamicField):
    name = limpyd_fields.PKField()
    tags = limpyd_fields.SetField(indexable=True)
    personal_tags = fields.DynamicSetField(indexable=True)


class DynamicFieldsTest(LimpydBaseTest):
    def setUp(self):
        super(DynamicFieldsTest, self).setUp()

        self.fight_club = Movie(name='Fight club')
        self.fight_club.tags.sadd('us', 'drama', 'brad pitt')

        self.matrix = Movie(name='Matrix')
        self.matrix.tags.sadd('us', 'action', 'keanu reaves')

        self.somebody = Person(name='Somebody')

    def test_dynamic_field_must_be_in_a_dynamic_model(self):
        with self.assertRaises(ImplementationError):
            class TestModel(TestRedisModel):
                namespace = 'test_dynamic_field_must_be_in_a_dynamic_model'
                test_field = fields.DynamicSetField()

    def test_dymanic_field_name_must_match(self):
        class TestModel(TestRedisModelWithDynamicField):
            namespace = 'test_dymanic_field_name_must_match'
            test_field = fields.DynamicSetField(pattern='^part_\d+$')

        instance = TestModel()
        # field ok
        instance.get_field('part_1')

        with self.assertRaises(ValueError):
            # the name does not match
            instance.get_field('part_two')

    def test_dynamic_field_names_should_be_dynamically_created(self):
        somebody_pk = self.somebody.pk.get()

        # manually compute the name
        tags_field_name = Movie.personal_tags.get_name_for(somebody_pk)
        self.assertEqual(tags_field_name, 'personal_tags_Somebody')

        # get the field using the final dynamic name
        fight_club_tags_field = self.fight_club.get_field(tags_field_name)
        self.assertEqual(fight_club_tags_field.name, tags_field_name)

        # get the field using only the dynamic part
        matrix_tags_field = self.matrix.personal_tags(somebody_pk)
        self.assertEqual(matrix_tags_field.name, tags_field_name)

    def test_set_and_get_dynamic_field(self):
        # set for one instance
        fight_club_somebody_tags = self.fight_club.personal_tags(self.somebody.pk.get())
        fight_club_somebody_tags.sadd('fight', 'cool')

        retrieved = fight_club_somebody_tags.smembers()
        attended = set(['fight', 'cool'])

        self.assertEqual(retrieved, attended)

        # set for another instance
        matrix_somebody_tags = self.matrix.personal_tags(self.somebody.pk.get())
        matrix_somebody_tags.sadd('sf', 'cool')

        retrieved = matrix_somebody_tags.smembers()
        attended = set(['sf', 'cool'])

        self.assertEqual(retrieved, attended)

        # set for another person
        someone_else = Person(name='Someone Else')

        fight_club_someoneelse_tags = self.fight_club.personal_tags(someone_else.pk.get())
        fight_club_someoneelse_tags.sadd('ikea', 'revolution')

        retrieved = fight_club_someoneelse_tags.smembers()
        attended = set(['ikea', 'revolution'])

        self.assertEqual(retrieved, attended)

    def test_model_could_handle_many_dynamic_fields(self):
        class TestModel(TestRedisModelWithDynamicField):
            namespace = 'test_model_could_handle_many_dynamic_fields'
            foo = fields.DynamicStringField()
            bar = fields.DynamicStringField()

        instance = TestModel()

        foo_field_1 = instance.get_field('foo_1')
        foo_field_2 = instance.get_field('foo_2')
        bar_field_1 = instance.get_field('bar_1')
        bar_field_2 = instance.get_field('bar_2')

        foo_field_1.set('foo1')
        foo_field_2.set('foo2')
        bar_field_1.set('bar1')
        bar_field_2.set('bar2')

        # reload
        instance = TestModel(instance.pk.get())
        self.assertEqual(instance.get_field('foo_1').get(), 'foo1')
        self.assertEqual(instance.get_field('foo_2').get(), 'foo2')
        self.assertEqual(instance.get_field('bar_1').get(), 'bar1')
        self.assertEqual(instance.get_field('bar_2').get(), 'bar2')

    def test_dynamic_field_could_be_set_on_constructor(self):
        class TestModel(TestRedisModelWithDynamicField):
            namespace = 'test_dynamic_field_could_be_set_on_constructor'
            name = limpyd_fields.StringField()
            test_field = fields.DynamicStringField()

        # create
        instance = TestModel(name='foo', test_field_1='foo 1', test_field_2='bar 2')

        # reload
        instance = TestModel(instance.pk.get())

        # test
        self.assertEqual(instance.name.get(), 'foo')
        self.assertEqual(instance.get_field('test_field_1').get(), 'foo 1')
        self.assertEqual(instance.get_field('test_field_2').get(), 'bar 2')

    def test_indexable_dynamic_fields_should_be_indexed(self):
        somebody_pk = self.somebody.pk.get()

        self.fight_club.personal_tags(somebody_pk).sadd('fight', 'cool')
        self.matrix.personal_tags(somebody_pk).sadd('sf', 'cool')

        attended = set(['Fight club', 'Matrix'])

        # using real named argument (but not usable if complex one, it's ok here)
        somebody_cool_movies = Movie.collection(personal_tags_Somebody='cool')
        self.assertEqual(set(somebody_cool_movies), attended)

        # using dict as collection arguments
        somebody_personal_tags = Movie.personal_tags.get_name_for(somebody_pk)
        arg_dict = {
            somebody_personal_tags: 'cool',
        }
        somebody_cool_movies = Movie.collection(**arg_dict)
        self.assertEqual(set(somebody_cool_movies), attended)

        # using new dynamic_filter method
        somebody_cool_movies = Movie.collection().dynamic_filter('personal_tags', somebody_pk, 'cool')
        self.assertEqual(set(somebody_cool_movies), attended)

    def test_normal_filters_could_be_filtered_with_dynamic_ones(self):
        somebody_pk = self.somebody.pk.get()

        self.fight_club.personal_tags(somebody_pk).sadd('fight', 'cool')
        self.matrix.personal_tags(somebody_pk).sadd('sf', 'cool')

        personal_cool_drama = Movie.collection(tags='drama') \
                                   .dynamic_filter('personal_tags', somebody_pk, 'cool')
        attended = set(['Fight club'])
        self.assertEqual(set(personal_cool_drama), attended)

    def test_dynamic_fields_should_work_for_strings(self):
        class TestModel(TestRedisModelWithDynamicField):
            namespace = 'test_dynamic_fields_should_work_for_strings'
            test_field = fields.DynamicStringField(indexable=True)

        instance = TestModel(test_field_1='foo')
        self.assertEqual(set(TestModel.collection(test_field_1='foo')), set([instance.pk.get()]))

    def test_dynamic_fields_should_work_for_instancehashes(self):
        class TestModel(TestRedisModelWithDynamicField):
            namespace = 'test_dynamic_fields_should_work_for_instancehashes'
            test_field = fields.DynamicInstanceHashField(indexable=True)

        instance = TestModel(test_field_1='foo')
        self.assertEqual(set(TestModel.collection(test_field_1='foo')), set([instance.pk.get()]))

        # calling hmget with the defined dynamic field
        self.assertEqual(instance.hmget('test_field_1'), ['foo'])

        # calling hmget with a non defined dynamic field
        self.assertEqual(instance.hmget('test_field_1', 'test_field_2'), ['foo', None])

        # calling hmget with two defined dynamic fields
        instance.get_field('test_field_2').hset('bar')
        self.assertEqual(instance.hmget('test_field_1', 'test_field_2'), ['foo', 'bar'])

        # calling hmget with an invalid dynamic field
        with self.assertRaises(ValueError):
            instance.hmget('test__field_1')

    def test_dynamic_fields_should_work_for_sets(self):
        class TestModel(TestRedisModelWithDynamicField):
            namespace = 'test_dynamic_fields_should_work_for_sets'
            test_field = fields.DynamicSetField(indexable=True)

        instance = TestModel()
        field = instance.get_field('test_field_1')
        field.sadd('foo', 'bar')
        self.assertEqual(set(TestModel.collection(test_field_1='foo')), set([instance.pk.get()]))

    def test_dynamic_fields_should_work_for_lists(self):
        class TestModel(TestRedisModelWithDynamicField):
            namespace = 'test_dynamic_fields_should_work_for_lists'
            test_field = fields.DynamicListField(indexable=True)

        instance = TestModel()
        field = instance.get_field('test_field_1')
        field.lpush('foo', 'bar')
        self.assertEqual(set(TestModel.collection(test_field_1='foo')), set([instance.pk.get()]))

    def test_dynamic_fields_should_work_for_sortedsets(self):
        class TestModel(TestRedisModelWithDynamicField):
            namespace = 'test_dynamic_fields_should_work_for_sortedsets'
            test_field = fields.DynamicSortedSetField(indexable=True)

        instance = TestModel()
        field = instance.get_field('test_field_1')
        field.zadd(foo=1, bar=2)
        self.assertEqual(set(TestModel.collection(test_field_1='foo')), set([instance.pk.get()]))

    def test_dynamic_fields_should_work_for_hashfields(self):
        class TestModel(TestRedisModelWithDynamicField):
            namespace = 'test_dynamic_fields_should_work_for_hashfields'
            test_field = fields.DynamicHashField(indexable=True)

        instance = TestModel()
        field = instance.get_field('test_field_1')
        field.hmset(**{'foo': 'FOO', 'bar': 'BAR'})
        self.assertEqual(instance.test_field('1').hget('foo'), 'FOO')
        self.assertEqual(set(TestModel.collection(test_field_1__foo='FOO')), set([instance.pk.get()]))
        self.assertEqual(set(TestModel.collection().dynamic_filter('test_field__foo', '1', 'FOO')), set([instance.pk.get()]))

    def test_inventory_should_be_filled_and_cleaned(self):
        somebody_pk = self.somebody.pk.get()
        someone_else = Person(name='Someone Else')
        someone_else_pk = someone_else.pk.get()

        fight_club_inventory = self.fight_club.personal_tags._inventory
        matrix_inventory = self.matrix.personal_tags._inventory

        self.assertEqual(fight_club_inventory.smembers(), set())
        self.assertEqual(matrix_inventory.smembers(), set())

        self.fight_club.personal_tags(somebody_pk).sadd('fight', 'cool')
        self.assertEqual(fight_club_inventory.smembers(), set([somebody_pk]))
        self.assertEqual(matrix_inventory.smembers(), set())

        self.fight_club.personal_tags(someone_else_pk).sadd('ikea', 'revolution')
        self.assertEqual(fight_club_inventory.smembers(), set([somebody_pk, someone_else_pk]))
        self.assertEqual(matrix_inventory.smembers(), set())

        self.matrix.personal_tags(somebody_pk).sadd('sf', 'cool')
        self.assertEqual(fight_club_inventory.smembers(), set([somebody_pk, someone_else_pk]))
        self.assertEqual(matrix_inventory.smembers(), set([somebody_pk]))

        self.matrix.personal_tags(somebody_pk).delete()
        self.assertEqual(fight_club_inventory.smembers(), set([somebody_pk, someone_else_pk]))
        self.assertEqual(matrix_inventory.smembers(), set())

        self.fight_club.personal_tags(someone_else_pk).delete()
        self.assertEqual(fight_club_inventory.smembers(), set([somebody_pk]))
        self.assertEqual(matrix_inventory.smembers(), set())

        self.fight_club.personal_tags(someone_else_pk).sadd('ikea', 'revolution')
        self.assertEqual(fight_club_inventory.smembers(), set([somebody_pk, someone_else_pk]))
        self.assertEqual(matrix_inventory.smembers(), set())
        self.fight_club.personal_tags.delete()
        self.assertEqual(fight_club_inventory.smembers(), set())
        self.assertEqual(matrix_inventory.smembers(), set())

