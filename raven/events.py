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
from raven.utils.stacks import get_stack_info, iter_traceback_frames

__all__ = ('BaseEvent', 'Exception', 'Message', 'Query')


class BaseEvent(object):
    def __init__(self, client):
        self.client = client
        self.logger = logging.getLogger(__name__)

    def to_string(self, data):
        raise NotImplementedError

    def capture(self, **kwargs):
        return {
        }

    def transform(self, value):
        return self.client.transform(value)


class Exception(BaseEvent):
    """
    Exceptions store the following metadata:

    - value: 'My exception value'
    - type: 'ClassName'
    - module '__builtin__' (i.e. __builtin__.TypeError)
    - frames: a list of serialized frames (see _get_traceback_frames)
    """

    def to_string(self, data):
        exc = data['sentry.interfaces.Exception']
        if exc['value']:
            return '%s: %s' % (exc['type'], exc['value'])
        return exc['type']

    def capture(self, exc_info=None, **kwargs):
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
                'level': kwargs.get('level', logging.ERROR),
                'sentry.interfaces.Exception': {
                    'value': to_unicode(exc_value),
                    'type': str(exc_type),
                    'module': to_unicode(exc_module),
                },
                'sentry.interfaces.Stacktrace': {
                    'frames': frames
                },
            }
        finally:
            try:
                del exc_type, exc_value, exc_traceback
            except Exception as e:
                self.logger.exception(e)


class Message(BaseEvent):
    """
    Messages store the following metadata:

    - message: 'My message from %s about %s'
    - params: ('foo', 'bar')
    """
    def capture(self, message, params=(), formatted=None, **kwargs):
        message = to_unicode(message)
        data = {
            'sentry.interfaces.Message': {
                'message': message,
                'params': self.transform(params),
            },
        }
        if 'message' not in data:
            data['message'] = formatted or message
        return data


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
