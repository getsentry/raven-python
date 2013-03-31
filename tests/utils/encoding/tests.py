# -*- coding: utf-8 -*-

import uuid

from raven.utils import six
from raven.utils.compat import TestCase
from raven.utils.serializer import transform


class TransformTest(TestCase):
    def test_incorrect_unicode(self):
        x = 'רונית מגן'

        result = transform(x)
        assert result == "'רונית מגן'"

    def test_correct_unicode(self):
        # 'רונית מגן'
        x = six.text_type('\u05e8\u05d5\u05e0\u05d9\u05ea \u05de\u05d2\u05df')

        result = transform(x)
        assert result == six.text_type("u'\u05e8\u05d5\u05e0\u05d9\u05ea \u05de\u05d2\u05df'")

    def test_bad_string(self):
        x = 'The following character causes problems: \xd4'

        result = transform(x)
        assert result == "<type 'str'>"

    def test_float(self):
        result = transform(13.0)
        self.assertEquals(type(result), float)
        self.assertEquals(result, 13.0)

    def test_bool(self):
        result = transform(True)
        self.assertEquals(type(result), bool)
        self.assertEquals(result, True)

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

    def test_dict_keys(self):
        x = {'foo': 'bar'}

        result = transform(x)
        self.assertEquals(type(result), dict)
        keys = result.keys()
        self.assertEquals(len(keys), 1)
        self.assertTrue(type(keys[0]), str)
        self.assertEquals(keys[0], "'foo'")

    def test_dict_keys_utf8_as_str(self):
        x = {'רונית מגן': 'bar'}

        result = transform(x)
        self.assertEquals(type(result), dict)
        keys = result.keys()
        self.assertEquals(len(keys), 1)
        assert keys[0] == "'רונית מגן'"

    def test_dict_keys_utf8_as_unicode(self):
        x = {
            six.text_type('\u05e8\u05d5\u05e0\u05d9\u05ea \u05de\u05d2\u05df'): 'bar'
        }

        result = transform(x)
        assert type(result) is dict
        keys = result.keys()
        assert len(keys) == 1
        assert keys[0] == six.text_type("u'\u05e8\u05d5\u05e0\u05d9\u05ea \u05de\u05d2\u05df'")

    def test_uuid(self):
        x = uuid.uuid4()
        result = transform(x)
        assert result == repr(x)

    def test_recursive(self):
        x = []
        x.append(x)

        result = transform(x)
        self.assertEquals(result, ('<...>',))

    def test_custom_repr(self):
        class Foo(object):
            def __sentry__(self):
                return 'example'

        x = Foo()

        result = transform(x)
        self.assertEquals(result, "'example'")

    def test_broken_repr(self):
        class Foo(object):
            def __repr__(self):
                raise ValueError

        x = Foo()

        result = transform(x)
        self.assertEquals(result, "<class 'tests.utils.encoding.tests.Foo'>")

    def test_recursion_max_depth(self):
        x = [[[[1]]]]
        result = transform(x, max_depth=3)
        self.assertEquals(result, ((("'[1]'",),),))

    def test_list_max_length(self):
        x = range(10)
        result = transform(x, list_max_length=3)
        self.assertEquals(result, (0, 1, 2))

    def test_dict_max_length(self):
        x = dict((x, x) for x in xrange(10))
        result = transform(x, list_max_length=3)
        self.assertEquals(type(x), dict)
        self.assertEquals(len(result), 3)

    def test_string_max_length(self):
        x = '1234'
        result = transform(x, string_max_length=3)
        self.assertEquals(result, "'123'")
