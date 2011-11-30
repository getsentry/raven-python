"""
raven.handlers.logbook
~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import logbook
import sys

class SentryHandler(logbook.Handler):
    def __init__(self, *args, **kwargs):
        try:
            self.client = kwargs.pop('client')
        except KeyError:
            raise TypeError('Expected keyword argument for SentryHandler: client')
        super(SentryHandler, self).__init__(*args, **kwargs)

    def emit(self, record):
        self.format(record)

        # Avoid typical config issues by overriding loggers behavior
        if record.channel.startswith('sentry.errors'):
            print >> sys.stderr, "Recursive log message sent to SentryHandler"
            print >> sys.stderr, record.message
            return

        kwargs = dict(
            message=record.message,
            level=record.level,
            logger=record.channel,
            data=record.extra,
        )
        if record.exc_info:
            return self.client.create_from_exception(record.exc_info, **kwargs)
        return self.client.create_from_text(**kwargs)

