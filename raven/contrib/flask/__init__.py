"""
raven.contrib.flask
~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

from flask import request
from flask.signals import got_request_exception
from raven.conf import setup_logging
from raven.base import Client
from raven.contrib.flask.utils import get_data_from_request
from raven.handlers.logging import SentryHandler


class Sentry(object):
    """
    Flask application for Sentry.

    >>> # Look up configuration from ``os.environ['SENTRY_DSN']``
    >>> sentry = Sentry(app)

    >>> # Pass an arbitrary dsn
    >>> sentry = Sentry(app, dsn='http://public:secret@example.com/1')

    >>> # Pass an explicit client
    >>> sentry = Sentry(app, client=client)

    >>> # Automatically configure logging
    >>> sentry = Sentry(app, logging=True)
    """
    def __init__(self, app=None, client=None, client_cls=Client, dsn=None,
                 logging=False):
        #self.app = app
        self.client_cls = client_cls
        self.dsn = dsn
        self.logging = logging
        self._client = client

        if app:
            self.init_app(app)

    @property
    def client(self):
        app = self.app
        if app is None:
            return None
        if self._client is None:
            self._client = self.client_cls(
                include_paths=set(app.config.get('SENTRY_INCLUDE_PATHS', [])) | set([app.import_name]),
                exclude_paths=app.config.get('SENTRY_EXCLUDE_PATHS'),
                servers=app.config.get('SENTRY_SERVERS'),
                name=app.config.get('SENTRY_NAME'),
                key=app.config.get('SENTRY_KEY'),
                public_key=app.config.get('SENTRY_PUBLIC_KEY'),
                secret_key=app.config.get('SENTRY_SECRET_KEY'),
                project=app.config.get('SENTRY_PROJECT'),
                site=app.config.get('SENTRY_SITE_NAME'),
                dsn=self.dsn or app.config.get('SENTRY_DSN'),
            )
        return self._client

    def handle_exception(self, client):
        def _handle_exception(*args, **kwargs):
            client.capture('Exception', exc_info=kwargs.get('exc_info'),
                data=get_data_from_request(request),
                extra={
                    'app': self.app,
                },
            )
        return _handle_exception

    def init_app(self, app):
        self.app = app
        if self.logging:
            setup_logging(SentryHandler(self.client))
        got_request_exception.connect(self.handle_exception(self.client), sender=app, weak=False)
