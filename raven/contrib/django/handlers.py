"""
raven.contrib.django.handlers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import logging
import sys
import traceback

class SentryHandler(logging.Handler):
    def emit(self, record):
        from raven.contrib.django.middleware import SentryLogMiddleware
        from raven.contrib.django.models import get_client

        # Fetch the request from a threadlocal variable, if available
        request = getattr(SentryLogMiddleware.thread, 'request', None)

        self.format(record)

        # Avoid typical config issues by overriding loggers behavior
        if record.name.startswith('sentry.errors'):
            print >> sys.stderr, "Recursive log message sent to SentryHandler"
            print >> sys.stderr, record.message
            return

        self.format(record)
        try:
            get_client().create_from_record(record, request=request)
        except Exception:
            print >> sys.stderr, "Top level Sentry exception caught - failed creating log record"
            print >> sys.stderr, record.msg
            print >> sys.stderr, traceback.format_exc()
            return

