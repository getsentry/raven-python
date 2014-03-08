"""
raven.events
~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import logging
import sys

from raven.utils.encoding import to_unicode
from raven.utils.stacks import (
    get_stack_info, iter_traceback_frames, iter_stack_frames,
)


__all__ = ('BaseEvent', 'Exception', 'Message', 'Query', 'get_handler')

handlers = {}


def register(cls):
    handlers[cls.__name__.lower()] = cls
    return cls


def get_handler(name):
    return handlers[name]


class BaseEvent(object):
    def __init__(self, client):
        self.client = client
        self.logger = logging.getLogger(__name__)

    def to_string(self, data):
        raise NotImplementedError

    def handle(self, stack=None, **kwargs):
        data = self.capture(**kwargs)
        data.setdefault('timestamp', kwargs['timestamp']),
        if 'data' in kwargs:
            data.update(**kwargs['data'])

        if stack and 'stacktrace' not in kwargs:
            if stack is True:
                frames = iter_stack_frames()
            else:
                frames = stack

            data.update({
                'stacktrace': {
                    'frames': get_stack_info(
                        frames, transformer=self.transform)
                },
            })

        if 'stacktrace' in kwargs:
            if self.client.include_paths:
                for frame in kwargs['stacktrace']['frames']:
                    if frame.get('in_app') is not None:
                        continue

                    module = frame.get('module')
                    abs_path = frame.get('abs_path')

                    if module and module[:6] == 'raven.':
                        frame['in_app'] = False
                    elif abs_path and '/site-packages/' in abs_path:
                        frame['in_app'] = False
                    elif module:
                        frame['in_app'] = (
                            any(module.startswith(x) for x in self.client.include_paths)
                            and not
                            any(module.startswith(x) for x in self.client.exclude_paths)
                        )

            data.update({
                'stacktrace': kwargs['stacktrace'],
            })
        return data

    def capture(self, **kwargs):
        raise NotImplementedError

    def transform(self, value):
        return self.client.transform(value)


@register
class Exception(BaseEvent):
    """
    Exceptions store the following metadata:

    - value: 'My exception value'
    - type: 'ClassName'
    - module '__builtin__' (i.e. __builtin__.TypeError)
    - frames: a list of serialized frames (see _get_traceback_frames)
    """

    def to_string(self, data):
        if data['value']:
            return '%s: %s' % (data['exc_type'], data['value'])
        return data['exc_type']

    def capture(self, exc_info=None, stack=None, **kwargs):
        if not exc_info or exc_info is True:
            exc_info = sys.exc_info()

        if not exc_info:
            raise ValueError('No exception found')

        exc_type, exc_value, exc_traceback = exc_info

        try:
            frames = get_stack_info(
                iter_traceback_frames(exc_traceback),
                transformer=self.transform)

            exc_module = getattr(exc_type, '__module__', None)
            if exc_module:
                exc_module = str(exc_module)
            exc_type = getattr(exc_type, '__name__', '<unknown>')

            return {
                'type': 'exception',
                'value': to_unicode(exc_value),
                'exc_type': str(exc_type),
                'module': to_unicode(exc_module),
                'stacktrace': {
                    'frames': frames
                },
            }
        finally:
            try:
                del exc_type, exc_value, exc_traceback
            except Exception as e:
                self.logger.exception(e)


@register
class Message(BaseEvent):
    """
    Messages store the following metadata:

    - message: 'My message from %s about %s'
    - params: ('foo', 'bar')
    """
    def to_string(self, data):
        return data['message']

    def capture(self, message, params=(), formatted=None, **kwargs):
        message = to_unicode(message)
        data = {
            'type': 'message',
            'message': message,
            'params': self.transform(params),
        }
        if 'message' not in data:
            data['message'] = formatted or message
        return data


@register
class Query(BaseEvent):
    """
    Messages store the following metadata:

    - query: 'SELECT * FROM table'
    - engine: 'postgesql_psycopg2'
    """
    def to_string(self, data):
        sql = data['sentry.interfaces.Query']
        return sql['query']

    def capture(self, query, engine, **kwargs):
        return {
            'sentry.interfaces.Query': {
                'query': to_unicode(query),
                'engine': str(engine),
            }
        }
