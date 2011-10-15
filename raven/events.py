"""
raven.events
~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import logging
import re
import sys

from sentry import app
from sentry.utils import transform

__all__ = ('BaseEvent', 'Exception', 'Message', 'Query')

class BaseEvent(object):
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
    interface = 'sentry.interfaces.Exception'

    def to_string(self, data):
        if data['value']:
            return '%s: %s' % (data['type'], data['value'])
        return data['type']

    def get_event_hash(self, type, value, **kwargs):
        # TODO: Need to add in the frames without line numbers
        return [type, value]

    def capture(self, exc_info=None, **kwargs):
        if exc_info is None:
            exc_info = sys.exc_info()

        exc_type, exc_value, exc_traceback = exc_info

        culprit = self._get_culprit(exc_info[2])

        if hasattr(exc_type, '__class__'):
            exc_module = exc_type.__class__.__module__
            if exc_module == '__builtin__':
                exc_type = exc_type.__name__
            else:
                exc_type = '%s.%s' % (exc_module, exc_type.__name__)
        else:
            exc_module = None
            exc_type = exc_type.__name__

        # if isinstance(exc_value, TemplateSyntaxError) and hasattr(exc_value, 'source'):
        #     origin, (start, end) = exc_value.source
        #     result['template'] = (origin.reload(), start, end, origin.name)
        #     result['tags'].append(('template', origin.loadname))

        return {
            'level': logging.ERROR,
            'culprit': culprit,
            'sentry.interfaces.Exception': {
                'value': transform(exc_value),
                'type': exc_type,
            },
            'sentry.interfaces.Stacktrace': {
                'frames': self._get_traceback_frames(exc_traceback)
            },
        }

    def _iter_tb(self, tb):
        while tb:
            # support for __traceback_hide__ which is used by a few libraries
            # to hide internal frames.
            if tb.tb_frame.f_locals.get('__traceback_hide__'):
                continue
            yield tb
            tb = tb.tb_next

    def _get_lines_from_file(self, filename, lineno, context_lines, loader=None, module_name=None):
        """
        Returns context_lines before and after lineno from file.
        Returns (pre_context_lineno, pre_context, context_line, post_context).
        """
        source = None
        if loader is not None and hasattr(loader, "get_source"):
            source = loader.get_source(module_name)
            if source is not None:
                source = source.splitlines()
        if source is None:
            try:
                f = open(filename)
                try:
                    source = f.readlines()
                finally:
                    f.close()
            except (OSError, IOError):
                pass
        if source is None:
            return None, [], None, []

        encoding = 'ascii'
        for line in source[:2]:
            # File coding may be specified. Match pattern from PEP-263
            # (http://www.python.org/dev/peps/pep-0263/)
            match = re.search(r'coding[:=]\s*([-\w.]+)', line)
            if match:
                encoding = match.group(1)
                break
        source = [unicode(sline, encoding, 'replace') for sline in source]

        lower_bound = max(0, lineno - context_lines)
        upper_bound = lineno + context_lines

        pre_context = [line.strip('\n') for line in source[lower_bound:lineno]]
        context_line = source[lineno].strip('\n')
        post_context = [line.strip('\n') for line in source[lineno+1:upper_bound]]

        return lower_bound, pre_context, context_line, post_context

    def _get_culprit(self, traceback):
        # We iterate through each frame looking for a deterministic culprit
        # When one is found, we mark it as last "best guess" (best_guess) and then
        # check it against SENTRY_EXCLUDE_PATHS. If it isnt listed, then we
        # use this option. If nothing is found, we use the "best guess".
        def contains(iterator, value):
            for k in iterator:
                if value.startswith(k):
                    return True
            return False

        if app.config['INCLUDE_PATHS']:
            modules = app.config['INCLUDE_PATHS']
        else:
            modules = []

        best_guess = None
        for tb in self._iter_tb(traceback):
            frame = tb.tb_frame
            try:
                culprit = '.'.join([frame.f_globals['__name__'], frame.f_code.co_name])
            except:
                continue
            if contains(modules, culprit):
                if not (contains(app.config['EXCLUDE_PATHS'], culprit) and best_guess):
                    best_guess = culprit
            elif best_guess:
                break

        return best_guess

    def _get_traceback_frames(self, tb):
        frames = []
        for tb in self._iter_tb(tb):
            filename = tb.tb_frame.f_code.co_filename
            function = tb.tb_frame.f_code.co_name
            lineno = tb.tb_lineno - 1
            loader = tb.tb_frame.f_globals.get('__loader__')
            module_name = tb.tb_frame.f_globals.get('__name__')
            pre_context_lineno, pre_context, context_line, post_context = self._get_lines_from_file(filename, lineno, 7, loader, module_name)
            if pre_context_lineno is not None:
                frames.append({
                    'id': id(tb),
                    'filename': filename,
                    'module': module_name,
                    'function': function,
                    'lineno': lineno + 1,
                    # TODO: vars need to be references
                    'vars': tb.tb_frame.f_locals,
                    'pre_context': pre_context,
                    'context_line': context_line,
                    'post_context': post_context,
                    'pre_context_lineno': pre_context_lineno + 1,
                })
        return frames

class Message(BaseEvent):
    """
    Messages store the following metadata:

    - message: 'My message from %s about %s'
    - params: ('foo', 'bar')
    """

    def to_string(self, data):
        return data['message'] % tuple(data.get('params', ()))

    def get_event_hash(self, message, params=(), **kwargs):
        return [message] + list(params)

    def capture(self, message, params=(), **kwargs):
        return {
            'sentry.interfaces.Message': {
                'message': message,
                'params': params,
            }
        }

class Query(BaseEvent):
    """
    Messages store the following metadata:

    - query: 'SELECT * FROM table'
    - engine: 'postgesql_psycopg2'
    """
    def to_string(self, data):
        return data['query']

    def get_event_hash(self, query, engine, **kwargs):
        return [query, engine]

    def capture(self, query, engine, **kwargs):
        return {
            'sentry.interfaces.Query': {
                'query': query,
                'engine': engine,
            }
        }