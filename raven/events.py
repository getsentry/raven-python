"""
raven.events
~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import logging
import sys

from raven.utils import varmap
from raven.utils.encoding import shorten, to_unicode
from raven.utils.stacks import get_stack_info, iter_traceback_frames, \
                               get_culprit

__all__ = ('BaseEvent', 'Exception', 'Message', 'Query')

class BaseEvent(object):
    def __init__(self, client):
        self.client = client

    def to_string(self, data):
        raise NotImplementedError

    def capture(self, **kwargs):
        return {
        }

class Exception(BaseEvent):
    """
    Exceptions store the following metadata:

    - value: 'My exception value'
    - type: 'module.ClassName'
    - frames: a list of serialized frames (see _get_traceback_frames)
    - template: 'template/name.html'
    """

    def to_string(self, data):
        exc = data['sentry.interfaces.Exception']
        if exc['value']:
            return '%s: %s' % (exc['type'], exc['value'])
        return exc['type']

    def get_hash(self, data):
        exc = data['sentry.interfaces.Exception']
        output = [exc['type'], exc['value']]
        for frame in data['sentry.interfaces.Stacktrace']['frames']:
            output.append(frame['module'])
            output.append(frame['function'])
        return output

    def capture(self, exc_info=None, **kwargs):
        new_exc_info = exc_info is None
        if new_exc_info:
            exc_info = sys.exc_info()

        try:
            exc_type, exc_value, exc_traceback = exc_info

            frames = varmap(shorten, get_stack_info(iter_traceback_frames(exc_traceback)))

            culprit = get_culprit(frames, self.client.include_paths, self.client.exclude_paths)

            if hasattr(exc_type, '__class__'):
                exc_module = exc_type.__class__.__module__
                if exc_module == '__builtin__':
                    exc_type = exc_type.__name__
                else:
                    exc_type = '%s.%s' % (exc_module, exc_type.__name__)
            else:
                exc_module = None
                exc_type = exc_type.__name__
        finally:
            if new_exc_info:
                del exc_info
        # if isinstance(exc_value, TemplateSyntaxError) and hasattr(exc_value, 'source'):
        #     origin, (start, end) = exc_value.source
        #     result['template'] = (origin.reload(), start, end, origin.name)
        #     result['tags'].append(('template', origin.loadname))

        return {
            'level': logging.ERROR,
            'culprit': culprit,
            'sentry.interfaces.Exception': {
                'value': to_unicode(exc_value),
                'type': exc_type,
            },
            'sentry.interfaces.Stacktrace': {
                'frames': frames
            },
        }

class Message(BaseEvent):
    """
    Messages store the following metadata:

    - message: 'My message from %s about %s'
    - params: ('foo', 'bar')
    """

    def to_string(self, data):
        msg = data['sentry.interfaces.Message']
        return msg['message'] % tuple(msg.get('params', ()))

    def get_hash(self, data):
        msg = data['sentry.interfaces.Message']
        return [msg['message']] + list(msg['params'])

    def capture(self, message, params=(), **kwargs):
        data = {
            'sentry.interfaces.Message': {
                'message': message,
                'params': params,
            }
        }
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

    def get_hash(self, data):
        sql = data['sentry.interfaces.Query']
        return [sql['query'], sql['engine']]

    def capture(self, query, engine, **kwargs):
        return {
            'sentry.interfaces.Query': {
                'query': query,
                'engine': engine,
            }
        }