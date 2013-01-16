"""
raven.handlers.logging
~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import datetime
import logging
import sys
import traceback

from raven.base import Client
from raven.utils.encoding import to_string
from raven.utils.stacks import iter_stack_frames

RESERVED = ('stack', 'name', 'module', 'funcName', 'args', 'msg', 'levelno', 'exc_text', 'exc_info', 'data', 'created', 'levelname', 'msecs', 'relativeCreated', 'tags')


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

        logging.Handler.__init__(self, level=kwargs.get('level', logging.NOTSET))

    def emit(self, record):
        try:
            self.format(record)

            # Avoid typical config issues by overriding loggers behavior
            if record.name.startswith('sentry.errors'):
                print >> sys.stderr, to_string(record.message)
                return

            return self._emit(record)
        except Exception:
            print >> sys.stderr, "Top level Sentry exception caught - failed creating log record"
            print >> sys.stderr, to_string(record.msg)
            print >> sys.stderr, to_string(traceback.format_exc())

            try:
                self.client.captureException()
            except Exception:
                pass

    def _emit(self, record, **kwargs):
        data = {}

        for k, v in record.__dict__.iteritems():
            if '.' not in k and k not in ('culprit',):
                continue
            data[k] = v

        stack = getattr(record, 'stack', None)
        if stack is True:
            stack = iter_stack_frames()

        if stack:
            # we might need to traverse this multiple times, so coerce it to a list
            stack = list(stack)
            frames = []
            started = False
            last_mod = ''
            for item in stack:
                if isinstance(item, (list, tuple)):
                    frame, lineno = item
                else:
                    frame, lineno = item, item.f_lineno

                if not started:
                    f_globals = getattr(frame, 'f_globals', {})
                    module_name = f_globals.get('__name__', '')
                    if (last_mod and last_mod.startswith('logging')) \
                        and not module_name.startswith('logging'):
                        started = True
                    else:
                        last_mod = module_name
                        continue
                frames.append((frame, lineno))

            # We must've not found a starting point
            if not frames:
                frames = stack

            stack = frames

        extra = getattr(record, 'data', None)
        if not isinstance(extra, dict):
            if extra:
                extra = {'data': extra}
            else:
                extra = {}

        # Add in all of the data from the record that we aren't already capturing
        for k in record.__dict__.keys():
            if k in RESERVED:
                continue
            if k.startswith('_'):
                continue
            extra[k] = record.__dict__[k]

        date = datetime.datetime.utcfromtimestamp(record.created)
        event_type = 'raven.events.Message'
        handler_kwargs = {'message': record.msg, 'params': record.args}
        if hasattr(record, 'tags'):
            handler_kwargs['tags'] = record.tags

        # If there's no exception being processed, exc_info may be a 3-tuple of None
        # http://docs.python.org/library/sys.html#sys.exc_info
        if record.exc_info and all(record.exc_info):
            # capture the standard message first so that we ensure
            # the event is recorded as an exception, in addition to having our
            # message interface attached
            handler = self.client.get_handler(event_type)
            data.update(handler.capture(**handler_kwargs))
            # ensure message is propagated, otherwise the exception will overwrite it
            data['message'] = handler.to_string(data)

            event_type = 'raven.events.Exception'
            handler_kwargs = {'exc_info': record.exc_info}

        # HACK: discover a culprit when we normally couldn't
        elif not (data.get('sentry.interfaces.Stacktrace') or data.get('culprit')) and (record.name or record.funcName):
            data['culprit'] = '%s in %s' % (record.name or '<unknown module>', record.funcName or '<unknown function>')

        data['level'] = record.levelno
        data['logger'] = record.name

        kwargs.update(handler_kwargs)

        return self.client.capture(event_type, stack=stack, data=data, extra=extra,
            date=date, **kwargs)
