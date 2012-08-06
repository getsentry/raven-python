"""
raven.contrib.django.serializers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from django.db.models.query import QuerySet
from django.utils.functional import Promise
from raven.utils.serializer import Serializer, register

__all__ = ('PromiseSerializer',)


class PromiseSerializer(Serializer):
    types = (Promise,)

    def serialize(self, value):
        # EPIC HACK
        # handles lazy model instances (which are proxy values that dont easily give you the actual function)
        pre = value.__class__.__name__[1:]
        if not hasattr(value, '%s__func' % pre):
            return value

        value = getattr(value, '%s__func' % pre)(*getattr(value, '%s__args' % pre), **getattr(value, '%s__kw' % pre))
        return self.recurse(value)


class QuerySetSerializer(Serializer):
    types = (QuerySet,)

    def serialize(self, value):
        qs_name = type(value).__name__
        if value.model:
            return u'<%s: model=%s>' % (qs_name, value.model.__name__)
        return u'<%s: (Unbound)>' % (qs_name,)


register(PromiseSerializer)
register(QuerySetSerializer)
