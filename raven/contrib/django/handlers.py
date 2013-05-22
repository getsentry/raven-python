"""
raven.contrib.django.handlers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import logging
from raven.handlers.logging import SentryHandler as BaseSentryHandler


class SentryHandler(BaseSentryHandler):
    def __init__(self):
        logging.Handler.__init__(self)

    def _get_client(self):
        from raven.contrib.django.models import client

        return client

    client = property(_get_client)

    def _emit(self, record):
        request = getattr(record, 'request', None)

        return super(SentryHandler, self)._emit(record, request=request)
