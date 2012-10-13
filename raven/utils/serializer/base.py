"""
raven.utils.serializer.base
~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from raven.utils.encoding import to_string, to_unicode
from raven.utils.serializer.manager import register
from types import ClassType, TypeType
from uuid import UUID

__all__ = ('Serializer',)


def has_sentry_metadata(value):
    try:
        return callable(value.__getattribute__('__sentry__'))
    except:
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

    def serialize(self, value):
        """
        Given ``value``, coerce into a JSON-safe type.
        """
        return value

    def recurse(self, value):
        """
        Given ``value``, recurse (using the parent serializer) to handle
        coercing of newly defined values.
        """
        return self.manager.transform(value)


class IterableSerializer(Serializer):
    types = (tuple, list, set, frozenset)

    def serialize(self, value):
        try:
            return type(value)(self.recurse(o) for o in value)
        except Exception:
            # We may be dealing with something like a namedtuple
            class value_type(list):
                __name__ = type(value).__name__
            return value_type(self.recurse(o) for o in value)


class UUIDSerializer(Serializer):
    types = (UUID,)

    def serialize(self, value):
        return repr(value)


class DictSerializer(Serializer):
    types = (dict,)

    def serialize(self, value):
        return dict((to_string(k), self.recurse(v)) for k, v in value.iteritems())


class UnicodeSerializer(Serializer):
    types = (unicode,)

    def serialize(self, value):
        return to_unicode(value)


class StringSerializer(Serializer):
    types = (str,)

    def serialize(self, value):
        return to_string(value)


class TypeSerializer(Serializer):
    types = (ClassType, TypeType,)

    def can(self, value):
        return not super(TypeSerializer, self).can(value) and has_sentry_metadata(value)

    def serialize(self, value):
        return self.recurse(value.__sentry__())


class BooleanSerializer(Serializer):
    types = (bool,)

    def serialize(self, value):
        return bool(value)


class FloatSerializer(Serializer):
    types = (float,)

    def serialize(self, value):
        return float(value)


class IntegerSerializer(Serializer):
    types = (int,)

    def serialize(self, value):
        return int(value)


class LongSerializer(Serializer):
    types = (long,)

    def serialize(self, value):
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
