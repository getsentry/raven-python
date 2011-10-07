# -*- coding: utf-8 -*-

import logging
from unittest2 import TestCase

from raven.utils.encoding import transform, shorten

logger = logging.getLogger('sentry.tests')

class TransformTest(TestCase):
    def test_incorrect_unicode(self):
        x = 'רונית מגן'

        result = transform(x)
        self.assertEquals(result, 'רונית מגן')

    def test_correct_unicode(self):
        x = 'רונית מגן'.decode('utf-8')

        result = transform(x)
        self.assertEquals(result, x)

    def test_bad_string(self):
        x = 'The following character causes problems: \xd4'

        result = transform(x)
        self.assertEquals(result, '<type \'str\'>')

    # def test_bad_string(self):
    #     x = 'The following character causes problems: \xd4'

    #     result = transform(x)
    #     self.assertEquals(result, '(Error decoding value)')

    # def test_model_instance(self):
    #     instance = DuplicateKeyModel(foo='foo')

    #     result = transform(instance)
    #     self.assertEquals(result, '<DuplicateKeyModel: foo>')

    # def test_handles_gettext_lazy(self):
    #     from django.utils.functional import lazy
    #     def fake_gettext(to_translate):
    #         return u'Igpay Atinlay'

    #     fake_gettext_lazy = lazy(fake_gettext, str)

    #     self.assertEquals(
    #         pickle.loads(pickle.dumps(
    #                 transform(fake_gettext_lazy("something")))),
    #         u'Igpay Atinlay')

    def test_dict_keys(self):
        x = {u'foo': 'bar'}

        result = transform(x)
        keys = result.keys()
        self.assertEquals(len(keys), 1)
        self.assertEquals(keys[0], 'foo')
        self.assertTrue(isinstance(keys[0], str))

    def test_uuid(self):
        import uuid

        uuid = uuid.uuid4()
        self.assertEquals(transform(uuid), repr(uuid))

class GetVersionsTest(TestCase):
    def test_get_versions(self):
        import raven
        from raven.utils import get_versions
        versions = get_versions(['raven'])
        self.assertEquals(versions.get('raven'), raven.VERSION)
        versions = get_versions(['raven.contrib.django'])
        self.assertEquals(versions.get('raven'), raven.VERSION)

class ShortenTest(TestCase):
    def test_shorten_string(self):
        result = shorten('hello world!', string_length=5)
        self.assertEquals(len(result), 8)
        self.assertEquals(result, 'hello...')

    def test_shorten_lists(self):
        result = shorten(range(500), list_length=50)
        self.assertEquals(len(result), 52)
        self.assertEquals(result[-2], '...')
        self.assertEquals(result[-1], '(450 more elements)')

    def test_shorten_sets(self):
        result = shorten(set(range(500)), list_length=50)
        self.assertEquals(len(result), 52)
        self.assertEquals(result[-2], '...')
        self.assertEquals(result[-1], '(450 more elements)')

    def test_shorten_frozenset(self):
        result = shorten(frozenset(range(500)), list_length=50)
        self.assertEquals(len(result), 52)
        self.assertEquals(result[-2], '...')
        self.assertEquals(result[-1], '(450 more elements)')

    def test_shorten_tuple(self):
        result = shorten(tuple(range(500)), list_length=50)
        self.assertEquals(len(result), 52)
        self.assertEquals(result[-2], '...')
        self.assertEquals(result[-1], '(450 more elements)')

    # def test_shorten_generator(self):
    #     result = shorten(xrange(500))
    #     self.assertEquals(len(result), 52)
    #     self.assertEquals(result[-2], '...')
    #     self.assertEquals(result[-1], '(450 more elements)')
