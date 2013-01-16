"""
raven.utils.serializer.base
~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import itertools
from raven.utils.encoding import to_string, to_unicode
from raven.utils.serializer.manager import register
from types import ClassType, TypeType
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
                value = repr(value)
            except Exception, e:
                self.manager.logger.exception(e)
                return unicode(type(value))
        return self.manager.transform(value, max_depth=max_depth, _depth=_depth, **kwargs)


class IterableSerializer(Serializer):
    types = (tuple, list, set, frozenset)

    def serialize(self, value, **kwargs):
        list_max_length = kwargs.get('list_max_length') or float('inf')
        return tuple(self.recurse(o, **kwargs) for n, o in itertools.takewhile(lambda x: x[0] < list_max_length, enumerate(value)))


class UUIDSerializer(Serializer):
    types = (UUID,)

    def serialize(self, value, **kwargs):
        return repr(value)


class DictSerializer(Serializer):
    types = (dict,)

    def serialize(self, value, **kwargs):
        list_max_length = kwargs.get('list_max_length') or float('inf')
        return dict(
            (to_string(k), self.recurse(v, **kwargs))
            for n, (k, v) in itertools.takewhile(lambda x: x[0] < list_max_length, enumerate(value.iteritems()))
        )


class UnicodeSerializer(Serializer):
    types = (unicode,)

    def serialize(self, value, **kwargs):
        string_max_length = kwargs.get('string_max_length', None)
        return to_unicode(value)[:string_max_length]


class StringSerializer(Serializer):
    types = (str,)

    def serialize(self, value, **kwargs):
        string_max_length = kwargs.get('string_max_length', None)
        return to_string(value)[:string_max_length]


class TypeSerializer(Serializer):
    types = (ClassType, TypeType,)

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


class LongSerializer(Serializer):
    types = (long,)

    def serialize(self, value, **kwargs):
        return long(value)


register(IterableSerializer)
register(UUIDSerializer)
register(DictSerializer)
register(UnicodeSerializer)
register(StringSerializer)
register(TypeSerializer)
register(BooleanSerializer)
register(FloatSerializer)
register(IntegerSerializer)
register(LongSerializer)
