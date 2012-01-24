"""
raven.handlers.logging
~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import datetime
import logging
import sys
import traceback

from raven.base import Client


class SentryHandler(logging.Handler, object):
    reserved = ['threadName', 'name', 'thread', 'created', 'process', 'processName', 'args', 'module',
                'filename', 'levelno', 'exc_text', 'pathname', 'lineno', 'msg', 'exc_info', 'funcName',
                'relativeCreated', 'levelname', 'msecs', 'data', 'stack', 'message']

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

    def _emit(self, record, **kwargs):
        # {'threadName': 'MainThread', 'name': 'foo', 'thread': 140735216916832, 'created': 1319164393.308008, 'process': 89141, 'processName': 'MainProcess', 'args': (), 'module': 'Unknown module', 'filename': None, 'levelno': 20, 'exc_text': None, 'pathname': None, 'lineno': None, 'msg': 'test', 'exc_info': (None, None, None), 'funcName': None, 'relativeCreated': 3441.9949054718018, 'levelname': 'INFO', 'msecs': 308.00795555114746}
        data = {}

        for k, v in record.__dict__.iteritems():
            if k in self.reserved:
                continue
            data[k] = v

        extra = getattr(record, 'data', {})

        date = datetime.datetime.utcfromtimestamp(record.created)

        # If there's no exception being processed, exc_info may be a 3-tuple of None
        # http://docs.python.org/library/sys.html#sys.exc_info
        if record.exc_info and all(record.exc_info):
            handler = self.client.get_handler('raven.events.Exception')

            data.update(handler.capture(exc_info=record.exc_info))

        data['level'] = record.levelno
        data['logger'] = record.name

        return self.client.capture('Message', message=record.msg, params=record.args,
                            stack=getattr(record, 'stack', None), data=data, extra=extra,
                            date=date, **kwargs)
