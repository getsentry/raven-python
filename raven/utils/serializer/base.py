# -*- coding: utf-8 -*-
"""
raven.utils.serializer.base
~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import itertools
from raven.utils import six
from raven.utils.encoding import to_unicode
from raven.utils.serializer.manager import register
from uuid import UUID

__all__ = ('Serializer',)


def has_sentry_metadata(value):
    try:
        return callable(value.__getattribute__('__sentry__'))
    except Exception:
        return False


class Serializer(object):
    types = ()

    def __init__(self, manager):
        self.manager = manager

    def can(self, value):
        """
        Given ``value``, return a boolean describing whether this
        serializer can operate on the given type
        """
        return isinstance(value, self.types)

    def serialize(self, value, **kwargs):
        """
        Given ``value``, coerce into a JSON-safe type.
        """
        return value

    def recurse(self, value, max_depth=6, _depth=0, **kwargs):
        """
        Given ``value``, recurse (using the parent serializer) to handle
        coercing of newly defined values.
        """
        _depth += 1
        if _depth >= max_depth:
            try:
                value = six.text_type(repr(value))
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.manager.logger.exception(e)
                return type(value)
        return self.manager.transform(value, max_depth=max_depth, _depth=_depth, **kwargs)


class IterableSerializer(Serializer):
    types = (tuple, list, set, frozenset)

    def serialize(self, value, **kwargs):
        list_max_length = kwargs.get('list_max_length') or float('inf')
        return tuple(
            self.recurse(o, **kwargs)
            for n, o
            in itertools.takewhile(lambda x: x[0] < list_max_length, enumerate(value))
        )


class UUIDSerializer(Serializer):
    types = (UUID,)

    def serialize(self, value, **kwargs):
        return repr(value)


class DictSerializer(Serializer):
    types = (dict,)

    def make_key(self, key):
        if not isinstance(key, six.string_types):
            return to_unicode(key)
        return key

    def serialize(self, value, **kwargs):
        list_max_length = kwargs.get('list_max_length') or float('inf')
        return dict(
            (self.make_key(self.recurse(k, **kwargs)), self.recurse(v, **kwargs))
            for n, (k, v)
            in itertools.takewhile(lambda x: x[0] < list_max_length, enumerate(six.iteritems(value)))
        )


class UnicodeSerializer(Serializer):
    types = (six.text_type,)

    def serialize(self, value, **kwargs):
        # try to return a reasonable string that can be decoded
        # correctly by the server so it doesnt show up as \uXXX for each
        # unicode character
        # e.g. we want the output to be like: "u'רונית מגן'"
        string_max_length = kwargs.get('string_max_length', None)
        return repr(six.text_type('%s')) % (value[:string_max_length],)


class StringSerializer(Serializer):
    types = (six.binary_type,)

    def serialize(self, value, **kwargs):
        string_max_length = kwargs.get('string_max_length', None)
        if six.PY3:
            return repr(value[:string_max_length])

        try:
            # Python2 madness: let's try to recover from developer's issues
            # Try to process the string as if it was a unicode.
            return "'" + value.decode('utf8')[:string_max_length].encode('utf8') + "'"
        except UnicodeDecodeError:
            pass

        return repr(value[:string_max_length])


class TypeSerializer(Serializer):
    types = six.class_types

    def can(self, value):
        return not super(TypeSerializer, self).can(value) and has_sentry_metadata(value)

    def serialize(self, value, **kwargs):
        return self.recurse(value.__sentry__(), **kwargs)


class BooleanSerializer(Serializer):
    types = (bool,)

    def serialize(self, value, **kwargs):
        return bool(value)


class FloatSerializer(Serializer):
    types = (float,)

    def serialize(self, value, **kwargs):
        return float(value)


class IntegerSerializer(Serializer):
    types = (int,)

    def serialize(self, value, **kwargs):
        return int(value)


if not six.PY3:
    class LongSerializer(Serializer):
        types = (long,)  # noqa

        def serialize(self, value, **kwargs):
            return long(value)  # noqa


register(IterableSerializer)
register(UUIDSerializer)
register(DictSerializer)
register(UnicodeSerializer)
register(StringSerializer)
register(TypeSerializer)
register(BooleanSerializer)
register(FloatSerializer)
register(IntegerSerializer)
if not six.PY3:
    register(LongSerializer)
