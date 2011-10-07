"""
raven.middleware
~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import sys
from raven.utils.wsgi import get_current_url

class Sentry(object):
    """
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
        event_id = self.client.create_from_exception(
            exc_info=exc_info,
            url=get_current_url(environ, strip_querystring=True),
            data={
                'META': environ,
            },
        )
        return event_id
