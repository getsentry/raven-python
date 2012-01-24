# -*- coding: utf-8 -*-

import logging
from mock import Mock
from unittest2 import TestCase

from raven.utils.encoding import transform, shorten
from raven.utils.stacks import get_culprit, get_stack_info

logger = logging.getLogger('sentry.tests')


class TransformTest(TestCase):
    def test_incorrect_unicode(self):
        x = 'רונית מגן'

        result = transform(x)
        self.assertEquals(type(result), str)
        self.assertEquals(result, 'רונית מגן')

    def test_correct_unicode(self):
        x = 'רונית מגן'.decode('utf-8')

        result = transform(x)
        self.assertEquals(type(result), unicode)
        self.assertEquals(result, x)

    def test_bad_string(self):
        x = 'The following character causes problems: \xd4'

        result = transform(x)
        self.assertEquals(type(result), str)
        self.assertEquals(result, '<type \'str\'>')

    def test_int_subclass(self):
        class X(int):
            pass

        result = transform(X())
        self.assertEquals(type(result), int)
        self.assertEquals(result, 0)

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
        self.assertEquals(type(result), dict)
        keys = result.keys()
        self.assertEquals(len(keys), 1)
        self.assertTrue(type(keys[0]), str)
        self.assertEquals(keys[0], 'foo')

    def test_dict_keys_utf8_as_str(self):
        x = {'רונית מגן': 'bar'}

        result = transform(x)
        self.assertEquals(type(result), dict)
        keys = result.keys()
        self.assertEquals(len(keys), 1)
        self.assertTrue(type(keys[0]), str)
        self.assertEquals(keys[0], 'רונית מגן')

    def test_dict_keys_utf8_as_unicode(self):
        x = {u'רונית מגן': 'bar'}

        result = transform(x)
        keys = result.keys()
        self.assertEquals(len(keys), 1)
        self.assertTrue(type(keys[0]), str)
        self.assertEquals(keys[0], 'רונית מגן')

    def test_uuid(self):
        import uuid

        uuid = uuid.uuid4()
        result = transform(uuid)
        self.assertEquals(result, repr(uuid))
        self.assertTrue(type(result), str)


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


class Context(object):
    def __init__(self, dict):
        self.dict = dict

    __getitem__ = lambda s, *a: s.dict.__getitem__(*a)
    __setitem__ = lambda s, *a: s.dict.__setitem__(*a)
    iterkeys = lambda s, *a: s.dict.iterkeys(*a)


class StackTest(TestCase):
    def test_get_culprit_bad_module(self):
        culprit = get_culprit([{
            'module': None,
            'function': 'foo',
        }])
        self.assertEquals(culprit, '<unknown>.foo')

        culprit = get_culprit([{
            'module': 'foo',
            'function': None,
        }])
        self.assertEquals(culprit, 'foo.<unknown>')

        culprit = get_culprit([{
        }])
        self.assertEquals(culprit, '<unknown>.<unknown>')

    def test_bad_locals_in_frame(self):
        frame = Mock()
        frame.f_locals = Context({
            'foo': 'bar',
            'biz': 'baz',
        })
        frame.f_lineno = 1
        frame.f_globals = {}
        frame.f_code.co_filename = __file__
        frame.f_code.co_name = __name__

        frames = [frame]
        results = get_stack_info(frames)
        self.assertEquals(len(results), 1)
        result = results[0]
        self.assertTrue('vars' in result)
        vars = result['vars']
        self.assertTrue(isinstance(vars, dict))
        self.assertTrue('foo' in vars)
        self.assertEquals(vars['foo'], 'bar')
        self.assertTrue('biz' in vars)
        self.assertEquals(vars['biz'], 'baz')
