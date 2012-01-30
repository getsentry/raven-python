"""
raven.handlers.logbook
~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import logbook
import sys
import traceback


class SentryHandler(logbook.Handler):
    def __init__(self, *args, **kwargs):
        try:
            self.client = kwargs.pop('client')
        except KeyError:
            raise TypeError('Expected keyword argument for SentryHandler: client')
        super(SentryHandler, self).__init__(*args, **kwargs)

    def emit(self, record):
        # from sentry.client.middleware import SentryLogMiddleware

        # # Fetch the request from a threadlocal variable, if available
        # request = getattr(SentryLogMiddleware.thread, 'request', None)

        self.format(record)

        # Avoid typical config issues by overriding loggers behavior
        if record.channel.startswith('sentry.errors'):
            print >> sys.stderr, record.message
            return

        try:
            return self._emit(record)
        except Exception:
            print >> sys.stderr, "Top level Sentry exception caught - failed creating log record"
            print >> sys.stderr, record.msg
            print >> sys.stderr, traceback.format_exc()

            try:
                self.client.capture('Exception')
            except Exception:
                pass

    def _emit(self, record):
        data = {
            'level': record.level,
            'logger': record.channel,
        }

        # If there's no exception being processed, exc_info may be a 3-tuple of None
        # http://docs.python.org/library/sys.html#sys.exc_info
        if record.exc_info and all(record.exc_info):
            handler = self.client.get_handler('raven.events.Exception')

            data.update(handler.capture(exc_info=record.exc_info))

        return self.client.capture('Message',
            message=record.message,
            data=data,
            extra=record.extra,
        )
