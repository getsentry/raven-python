"""
raven.core.processors
~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

class Processor(object):
    def __init__(self, client):
        self.client = client

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
                        for k, v in frame['vars'].iteritems():
                            if 'password' in k or 'secret' in k:
                                # store mask as a fixed length for security
                                frame['vars'][k] = '*'*16
        return data