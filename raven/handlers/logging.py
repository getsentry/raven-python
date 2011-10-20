"""
raven.handlers.logging
~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import logging
import sys
import traceback

from raven.base import Client


class SentryHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        if len(args) == 1:
            self.client = args[0]
        elif 'client' in kwargs:
            self.client = kwargs['client']
        elif len(args) == 2 and not kwargs:
            servers, key = args
            self.client = Client(servers=servers, key=key)
        else:
            self.client = Client(*args, **kwargs)

        logging.Handler.__init__(self)

    def emit(self, record):
        # from sentry.client.middleware import SentryLogMiddleware

        # # Fetch the request from a threadlocal variable, if available
        # request = getattr(SentryLogMiddleware.thread, 'request', None)

        self.format(record)

        # Avoid typical config issues by overriding loggers behavior
        if record.name == 'sentry.errors':
            print >> sys.stderr, "Recursive log message sent to SentryHandler"
            print >> sys.stderr, record.message
            return

        self.format(record)
        try:
            self.client.create_from_record(record)
        except Exception:
            print >> sys.stderr, "Top level Sentry exception caught - failed creating log record"
            print >> sys.stderr, record.msg
            print >> sys.stderr, traceback.format_exc()
            return

