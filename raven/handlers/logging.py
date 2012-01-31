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
from raven.utils.stacks import iter_stack_frames


class SentryHandler(logging.Handler, object):
    def __init__(self, *args, **kwargs):
        client = kwargs.get('client_cls', Client)
        if len(args) == 1:
            arg = args[0]
            if isinstance(arg, basestring):
                self.client = client(dsn=arg)
            elif isinstance(arg, Client):
                self.client = arg
            else:
                raise ValueError('The first argument to %s must be either a Client instance or a DSN, got %r instead.' % (
                    self.__class__.__name__,
                    arg,
                ))
        elif 'client' in kwargs:
            self.client = kwargs['client']
        elif len(args) == 2 and not kwargs:
            servers, key = args
            self.client = client(servers=servers, key=key)
        else:
            self.client = client(*args, **kwargs)

        logging.Handler.__init__(self)

    def emit(self, record):
        # from sentry.client.middleware import SentryLogMiddleware

        # # Fetch the request from a threadlocal variable, if available
        # request = getattr(SentryLogMiddleware.thread, 'request', None)

        self.format(record)

        # Avoid typical config issues by overriding loggers behavior
        if record.name.startswith('sentry.errors'):
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
        data = {}

        for k, v in record.__dict__.iteritems():
            if '.' not in k:
                continue
            data[k] = v

        stack = getattr(record, 'stack', None)
        if stack is True:
            stack = iter_stack_frames()

        if stack:
            frames = []
            started = False
            last_mod = ''
            for frame in iter_stack_frames():
                if not started:
                    f_globals = getattr(frame, 'f_globals', {})
                    module_name = f_globals.get('__name__', '')
                    if last_mod.startswith('logging') and not module_name.startswith('logging'):
                        started = True
                    else:
                        last_mod = module_name
                        continue
                frames.append(frame)
            stack = frames

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
                            stack=stack, data=data, extra=extra,
                            date=date, **kwargs)
