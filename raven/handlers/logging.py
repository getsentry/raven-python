"""
raven.handlers.logging
~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import
from __future__ import print_function

import datetime
import logging
import sys
import traceback

from raven.base import Client
from raven.utils import six
from raven.utils.encoding import to_string
from raven.utils.stacks import iter_stack_frames, label_from_frame

RESERVED = ('stack', 'name', 'module', 'funcName', 'args', 'msg', 'levelno', 'exc_text', 'exc_info', 'data', 'created', 'levelname', 'msecs', 'relativeCreated', 'tags')


class SentryHandler(logging.Handler, object):
    def __init__(self, *args, **kwargs):
        client = kwargs.get('client_cls', Client)
        if len(args) == 1:
            arg = args[0]
            if isinstance(arg, six.string_types):
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
            # Beware to python3 bug (see #10805) if exc_info is (None, None, None)
            self.format(record)

            # Avoid typical config issues by overriding loggers behavior
            if record.name.startswith(('sentry.errors', 'raven')) or record.module.startswith('raven'):
                print(to_string(record.message), sys.stderr)
                return

            return self._emit(record)
        except Exception:
            print("Top level Sentry exception caught - failed creating log record", sys.stderr)
            print(to_string(record.msg), sys.stderr)
            print(to_string(traceback.format_exc()), sys.stderr)

    def _get_targetted_stack(self, stack):
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
                if ((last_mod and last_mod.startswith('logging'))
                        and not module_name.startswith('logging')):
                    started = True
                else:
                    last_mod = module_name
                    continue

            frames.append((frame, lineno))

        # We failed to find a starting point
        if not frames:
            return stack

        return frames

    def _emit(self, record, **kwargs):
        data = {}

        extra = getattr(record, 'data', None)
        if not isinstance(extra, dict):
            if extra:
                extra = {'data': extra}
            else:
                extra = {}

        for k, v in six.iteritems(vars(record)):
            if k in RESERVED:
                continue
            if k.startswith('_'):
                continue
            if '.' not in k and k not in ('culprit',):
                extra[k] = v
            else:
                data[k] = v

        stack = getattr(record, 'stack', None)
        if stack is True:
            stack = iter_stack_frames()

        if stack:
            stack = self._get_targetted_stack(stack)

        date = datetime.datetime.utcfromtimestamp(record.created)
        event_type = 'raven.events.Message'
        handler_kwargs = {
            'message': record.msg,
            'params': record.args,
            'formatted': record.message,
        }

        # If there's no exception being processed, exc_info may be a 3-tuple of None
        # http://docs.python.org/library/sys.html#sys.exc_info
        if record.exc_info and all(record.exc_info):
            # capture the standard message first so that we ensure
            # the event is recorded as an exception, in addition to having our
            # message interface attached
            handler = self.client.get_handler(event_type)
            data.update(handler.capture(**handler_kwargs))

            event_type = 'raven.events.Exception'
            handler_kwargs = {'exc_info': record.exc_info}

        # HACK: discover a culprit when we normally couldn't
        elif not (data.get('sentry.interfaces.Stacktrace') or data.get('culprit')) and (record.name or record.funcName):
            culprit = label_from_frame({'module': record.name, 'function': record.funcName})
            if culprit:
                data['culprit'] = culprit

        data['level'] = record.levelno
        data['logger'] = record.name

        if hasattr(record, 'tags'):
            kwargs['tags'] = record.tags

        kwargs.update(handler_kwargs)

        return self.client.capture(
            event_type, stack=stack, data=data,
            extra=extra, date=date, **kwargs)
