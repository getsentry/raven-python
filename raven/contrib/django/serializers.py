"""
raven.contrib.django.serializers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from django.utils.functional import Promise
from raven.utils.serializer import Serializer, register

__all__ = ('PromiseSerializer',)


@register
class PromiseSerializer(Serializer):
    types = (Promise,)

    def serialize(self, value):
        # EPIC HACK
        # handles lazy model instances (which are proxy values that dont easily give you the actual function)
        pre = value.__class__.__name__[1:]
        value = getattr(value, '%s__func' % pre)(*getattr(value, '%s__args' % pre), **getattr(value, '%s__kw' % pre))
        return self.recurse(value)
