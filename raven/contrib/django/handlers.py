"""
raven.contrib.django.handlers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

from raven.contrib.django.models import client
from raven.handlers.logging import SentryHandler as BaseSentryHandler


class SentryHandler(BaseSentryHandler):
    def __init__(self, *args, **kwargs):
        super(SentryHandler, self).__init__(client=client, *args, **kwargs)

    def _emit(self, record):
        request = getattr(record, 'request', None)
        return super(SentryHandler, self)._emit(record, request=request)
