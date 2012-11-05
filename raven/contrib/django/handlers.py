"""
raven.contrib.django.handlers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import logging

from django.conf import settings as django_settings
from raven.handlers.logging import SentryHandler as BaseSentryHandler


class SentryHandler(BaseSentryHandler):
    def __init__(self):
        logging.Handler.__init__(self)

    def _get_client(self):
        from raven.contrib.django.models import client

        return client

    client = property(_get_client)

    def _emit(self, record):
        from raven.contrib.django.middleware import SentryLogMiddleware

        # If we've explicitly enabled signals, or we're not running DEBUG, emit the record
        if getattr(django_settings, 'RAVEN_CONFIG', {}).get('register_signals', not django_settings.DEBUG):

            # Fetch the request from a threadlocal variable, if available
            request = getattr(record, 'request', getattr(SentryLogMiddleware.thread, 'request', None))

            return super(SentryHandler, self)._emit(record, request=request)
