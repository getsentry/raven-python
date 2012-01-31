"""
raven.middleware
~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import sys
from raven.utils.wsgi import get_current_url, get_headers, \
  get_environ


class Sentry(object):
    """
    A WSGI middleware which will attempt to capture any
    uncaught exceptions and send them to Sentry.

    >>> from raven.base import Client
    >>> application = Sentry(application, Client())
    """
    def __init__(self, application, client):
        self.application = application
        self.client = client

    def __call__(self, environ, start_response):
        try:
            for event in self.application(environ, start_response):
                yield event
        except Exception:
            exc_info = sys.exc_info()
            self.handle_exception(exc_info, environ)
            exc_info = None
            raise

    def handle_exception(self, exc_info, environ):
        event_id = self.client.capture('Exception',
            exc_info=exc_info,
            data={
                'sentry.interfaces.Http': {
                    'method': environ.get('REQUEST_METHOD'),
                    'url': get_current_url(environ, strip_querystring=True),
                    'query_string': environ.get('QUERY_STRING'),
                    # TODO
                    # 'data': environ.get('wsgi.input'),
                    'headers': dict(get_headers(environ)),
                    'env': dict(get_environ(environ)),
                }
            },
        )
        return event_id
