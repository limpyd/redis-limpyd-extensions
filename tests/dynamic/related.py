# -*- coding:utf-8 -*-


from limpyd import fields as limpyd_fields

from limpyd_extensions import related
from limpyd_extensions.dynamic import fields as dyn_fields, related as dyn_related

from ..base import LimpydBaseTest


class TestRedisModel(related.RelatedModel):
    """
    Use it as a base for all models created for tests
    """
    database = LimpydBaseTest.database
    abstract = True
    namespace = "dynamic-related-tests"


class TestRedisModelWithDynamicField(dyn_fields.ModelWithDynamicFieldMixin, TestRedisModel):
    abstract = True


class Tag(TestRedisModel):
    slug = limpyd_fields.PKField()


class Person(TestRedisModel):
    name = limpyd_fields.PKField()


class Movie(TestRedisModelWithDynamicField):
    name = limpyd_fields.PKField()
    tags = related.M2MSetField(Tag, related_name='movies')  # global public tags
    personal_tags = dyn_related.DynamicM2MSetField(Tag, related_name='movies_for_people')  # private tags for each person


class TestDynamicRelatedFields(LimpydBaseTest):

    def setUp(self):
        super(TestDynamicRelatedFields, self).setUp()

        # create some tags
        self.tags = dict(
            # some tags to use as main tags
            us = Tag(slug='us'),
            drama = Tag(slug='drama'),
            brad_pitt = Tag(slug='brad pitt'),
            action = Tag(slug='action'),
            keanu_reaves = Tag(slug='keanu reaves'),
            # some tags to use as personal ones
            fight = Tag(slug='fight'),
            cool = Tag(slug='cool'),
            sf = Tag(slug='sf'),
            ikea = Tag(slug='ikea'),
            revolution = Tag(slug='revolution'),
        )

        # add a film
        self.fight_club = Movie(name='Fight club')
        # and tag it
        self.fight_club.tags.sadd(self.tags['us'], self.tags['drama'], self.tags['brad_pitt'])

        # add another film
        self.matrix = Movie(name='Matrix')
        # and tag it
        self.matrix.tags.sadd(self.tags['us'], self.tags['action'], self.tags['keanu_reaves'])

        # and add a person
        self.somebody = Person(name='Somebody')
        self.someone_else = Person(name='Someone Else')

    def test_dynamic_related_field_should_be_dynamically_created(self):
        attended = 'personal_tags_Somebody'

        # manually compute the name, using the pk
        tags_field_name = Movie.personal_tags.get_name_for(self.somebody.pk.get())
        self.assertEqual(tags_field_name, attended)

        # same using the instance, not the pk
        tags_field_name = Movie.personal_tags.get_name_for(self.somebody)
        self.assertEqual(tags_field_name, attended)

        # use the callable, with the pk
        tags_field = self.fight_club.personal_tags(self.somebody.pk.get())
        self.assertEqual(tags_field.name, attended)

        # same using the instance, not the pk
        tags_field = self.fight_club.personal_tags(self.somebody)
        self.assertEqual(tags_field.name, attended)

    def test_set_and_get_dynamic_related_field(self):
        # set for one instance
        self.fight_club.personal_tags(self.somebody).sadd(self.tags['fight'], self.tags['cool'])

        retrieved = self.fight_club.personal_tags(self.somebody).smembers()
        attended = set([self.tags['fight'].pk.get(), self.tags['cool'].pk.get()])

        self.assertEqual(retrieved, attended)

        # set for another instance
        self.matrix.personal_tags(self.somebody).sadd(self.tags['sf'], self.tags['cool'])

        retrieved = self.matrix.personal_tags(self.somebody).smembers()
        attended = set([self.tags['sf'].pk.get(), self.tags['cool'].pk.get()])

        self.assertEqual(retrieved, attended)

        # set for another person
        self.fight_club.personal_tags(self.someone_else).sadd(self.tags['ikea'], self.tags['revolution'])

        retrieved = self.fight_club.personal_tags(self.someone_else).smembers()
        attended = set([self.tags['ikea'].pk.get(), self.tags['revolution'].pk.get()])

        self.assertEqual(retrieved, attended)

    def test_dynamic_related_field_should_work_in_collections(self):
        self.fight_club.personal_tags(self.somebody).sadd(self.tags['fight'], self.tags['cool'])
        self.matrix.personal_tags(self.somebody).sadd(self.tags['sf'], self.tags['cool'])

        # filter only on the dynamic field
        collection = Movie.collection().dynamic_filter('personal_tags', self.somebody, self.tags['cool'])
        attended = set([self.fight_club.pk.get(), self.matrix.pk.get()])
        self.assertEqual(set(collection), attended)

        # filter with normal field too
        collection = Movie.collection(tags=self.tags['drama']).dynamic_filter('personal_tags', self.somebody, self.tags['cool'])
        attended = set([self.fight_club.pk.get(), ])
        self.assertEqual(set(collection), attended)

    def test_related_collection_should_work_for_each_dynamic_variation(self):
        self.fight_club.personal_tags(self.somebody).sadd(self.tags['fight'], self.tags['cool'])
        self.matrix.personal_tags(self.somebody).sadd(self.tags['sf'], self.tags['cool'])

        # filter only the dynamic field
        collection = self.tags['cool'].movies_for_people(self.somebody)
        attended = set([self.fight_club.pk.get(), self.matrix.pk.get()])
        self.assertEqual(set(collection), attended)

        # filter with normal field too
        collection = self.tags['cool'].movies_for_people(self.somebody, tags=self.tags['drama'])
        attended = set([self.fight_club.pk.get(), ])
        self.assertEqual(set(collection), attended)

    def test_dynamic_related_field_should_work_with_fkstringfield(self):
        class Tag(TestRedisModel):
            namespace = 'test_dynamic_related_field_should_work_with_fkstringfield'
            slug = limpyd_fields.PKField()

        class Book(TestRedisModelWithDynamicField):
            namespace = 'test_dynamic_related_field_should_work_with_fkstringfield'
            name = limpyd_fields.PKField()
            personal_main_tag = dyn_related.DynamicFKStringField(Tag, related_name='books')

        horror = Tag(slug='horror')
        fiction = Tag(slug='fiction')

        it = Book(name='It')
        carry = Book(name='Carry')
        contact = Book(name='Contact')

        it.personal_main_tag(self.somebody).set(horror)
        carry.personal_main_tag(self.somebody).set(horror)
        contact.personal_main_tag(self.somebody).set(fiction)

        somebody_it_main_tag = it.personal_main_tag(self.somebody).get()
        self.assertEqual(somebody_it_main_tag, horror.pk.get())

        somebody_horror_books = horror.books(self.somebody)
        self.assertEqual(set(somebody_horror_books), set([it.pk.get(), carry.pk.get()]))

        somebody_fiction_books = fiction.books(self.somebody)
        self.assertEqual(set(somebody_fiction_books), set([contact.pk.get(), ]))

    def test_dynamic_related_field_should_work_with_fkinstancehashfield(self):
        class Tag(TestRedisModel):
            namespace = 'test_dynamic_related_field_should_work_with_fkinstancehashfield'
            slug = limpyd_fields.PKField()

        class Book(TestRedisModelWithDynamicField):
            namespace = 'test_dynamic_related_field_should_work_with_fkinstancehashfield'
            name = limpyd_fields.PKField()
            personal_main_tag = dyn_related.DynamicFKInstanceHashField(Tag, related_name='books')

        horror = Tag(slug='horror')
        fiction = Tag(slug='fiction')

        it = Book(name='It')
        carry = Book(name='Carry')
        contact = Book(name='Contact')

        it.personal_main_tag(self.somebody).hset(horror)
        carry.personal_main_tag(self.somebody).hset(horror)
        contact.personal_main_tag(self.somebody).hset(fiction)

        somebody_it_main_tag = it.personal_main_tag(self.somebody).hget()
        self.assertEqual(somebody_it_main_tag, horror.pk.get())

        somebody_horror_books = horror.books(self.somebody)
        self.assertEqual(set(somebody_horror_books), set([it.pk.get(), carry.pk.get()]))

        somebody_fiction_books = fiction.books(self.somebody)
        self.assertEqual(set(somebody_fiction_books), set([contact.pk.get(), ]))

    def test_dynamic_related_field_should_work_with_m2mlistfield(self):
        class Tag(TestRedisModel):
            namespace = 'test_dynamic_related_field_should_work_with_m2mlistfield'
            slug = limpyd_fields.PKField()

        class Movie(TestRedisModelWithDynamicField):
            namespace = 'test_dynamic_related_field_should_work_with_m2mlistfield'
            name = limpyd_fields.PKField()
            personal_tags = dyn_related.DynamicM2MListField(Tag, related_name='movies_for_people')

        fight_club = Movie(name='Fight club')
        matrix = Movie(name='Matrix')

        fight = Tag(slug='fight')
        cool = Tag(slug='cool')
        sf = Tag(slug='sf')

        fight_club.personal_tags(self.somebody).rpush(fight, cool)
        matrix.personal_tags(self.somebody).rpush(sf, cool)

        somebody_fight_club_tags = fight_club.personal_tags(self.somebody).lrange(0, -1)
        attended = [fight.pk.get(), cool.pk.get()]
        self.assertEqual(somebody_fight_club_tags, attended)

        somebody_matrix_tags = matrix.personal_tags(self.somebody).lrange(0, -1)
        attended = [sf.pk.get(), cool.pk.get()]
        self.assertEqual(somebody_matrix_tags, attended)

        somebody_cool_movies = cool.movies_for_people(self.somebody)
        attended = set([fight_club.pk.get(), matrix.pk.get()])
        self.assertEqual(set(somebody_cool_movies), attended)

        somebody_fight_movies = sf.movies_for_people(self.somebody)
        attended = set([matrix.pk.get(), ])
        self.assertEqual(set(somebody_fight_movies), attended)

    def test_dynamic_related_field_should_work_with_m2msortedsetfield(self):
        class Tag(TestRedisModel):
            namespace = 'test_dynamic_related_field_should_work_with_m2msortedsetfield'
            slug = limpyd_fields.PKField()

        class Movie(TestRedisModelWithDynamicField):
            namespace = 'test_dynamic_related_field_should_work_with_m2msortedsetfield'
            name = limpyd_fields.PKField()
            personal_tags = dyn_related.DynamicM2MSortedSetField(Tag, related_name='movies_for_people')

        fight_club = Movie(name='Fight club')
        matrix = Movie(name='Matrix')

        fight = Tag(slug='fight')
        cool = Tag(slug='cool')
        sf = Tag(slug='sf')

        fight_club.personal_tags(self.somebody).zadd(1, fight, 2, cool)
        matrix.personal_tags(self.somebody).zadd(3, sf, 1, cool)

        somebody_fight_club_tags = fight_club.personal_tags(self.somebody).zrange(0, -1)
        attended = [fight.pk.get(), cool.pk.get()]
        self.assertEqual(somebody_fight_club_tags, attended)

        somebody_matrix_tags = matrix.personal_tags(self.somebody).zrange(0, -1)
        attended = [cool.pk.get(), sf.pk.get()]
        self.assertEqual(somebody_matrix_tags, attended)

        somebody_cool_movies = cool.movies_for_people(self.somebody)
        attended = set([fight_club.pk.get(), matrix.pk.get()])
        self.assertEqual(set(somebody_cool_movies), attended)

        somebody_fight_movies = sf.movies_for_people(self.somebody)
        attended = set([matrix.pk.get(), ])
        self.assertEqual(set(somebody_fight_movies), attended)

    def test_inventory_should_be_filled_and_cleaned(self):
        somebody_pk = self.somebody.pk.get()
        someone_else_pk = self.someone_else.pk.get()

        fight_club_inventory = self.fight_club.personal_tags._inventory
        matrix_inventory = self.matrix.personal_tags._inventory

        self.assertEqual(fight_club_inventory.smembers(), set())
        self.assertEqual(matrix_inventory.smembers(), set())

        self.fight_club.personal_tags(self.somebody).sadd(self.tags['fight'], self.tags['cool'])
        self.assertEqual(fight_club_inventory.smembers(), set([somebody_pk]))
        self.assertEqual(matrix_inventory.smembers(), set())

        self.fight_club.personal_tags(self.someone_else).sadd(self.tags['ikea'], self.tags['revolution'])
        self.assertEqual(fight_club_inventory.smembers(), set([somebody_pk, someone_else_pk]))
        self.assertEqual(matrix_inventory.smembers(), set())

        self.matrix.personal_tags(self.somebody).sadd(self.tags['sf'], self.tags['cool'])
        self.assertEqual(fight_club_inventory.smembers(), set([somebody_pk, someone_else_pk]))
        self.assertEqual(matrix_inventory.smembers(), set([somebody_pk]))

        self.matrix.personal_tags(self.somebody).delete()
        self.assertEqual(fight_club_inventory.smembers(), set([somebody_pk, someone_else_pk]))
        self.assertEqual(matrix_inventory.smembers(), set())

        self.fight_club.personal_tags(self.someone_else).delete()
        self.assertEqual(fight_club_inventory.smembers(), set([somebody_pk]))
        self.assertEqual(matrix_inventory.smembers(), set())

        self.fight_club.personal_tags(self.someone_else).sadd(self.tags['ikea'], self.tags['revolution'])
        self.assertEqual(fight_club_inventory.smembers(), set([somebody_pk, someone_else_pk]))
        self.assertEqual(matrix_inventory.smembers(), set())
        self.fight_club.personal_tags.delete()
        self.assertEqual(fight_club_inventory.smembers(), set())
        self.assertEqual(matrix_inventory.smembers(), set())
