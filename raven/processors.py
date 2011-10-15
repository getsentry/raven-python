"""
raven.core.processors
~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import logging

from sentry import app

_CACHE = None
def all(from_cache=True):
    global _CACHE

    if _CACHE is None or not from_cache:
        modules = []
        for path in app.config['PROCESSORS']:
            module_name, class_name = path.rsplit('.', 1)
            try:
                module = __import__(module_name, {}, {}, class_name)
                handler = getattr(module, class_name)
            except Exception:
                logger = logging.getLogger(__name__)
                logger.exception('Unable to import %s' % (path,))
                continue
            modules.append(handler())

        _CACHE = modules

    for f in _CACHE:
        yield f

class Processor(object):
    def process(self, data, **kwargs):
        resp = self.get_data(data)
        if resp:
            data = resp
        return data

class SantizePasswordsProcessor(Processor):
    """
    Asterisk out passwords from password fields in frames.
    """
    def process(self, data, **kwargs):
        if 'sentry.interfaces.Stacktrace' in data:
            if 'frames' in data['sentry.interfaces.Stacktrace']:
                for frame in data['sentry.interfaces.Stacktrace']['frames']:
                    if 'vars' in frame:
                        for k,v in frame['vars'].iteritems():
                            if k.startswith('password'):
                                # store mask as a fixed length for security
                                frame['vars'][k] = '*'*16
        return data