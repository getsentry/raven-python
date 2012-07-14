"""
raven.contrib.flask
~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import os

from flask import request
from flask.signals import got_request_exception
from raven.conf import setup_logging
from raven.base import Client
from raven.contrib.flask.utils import get_data_from_request
from raven.handlers.logging import SentryHandler


def make_client(client_cls, app, dsn=None):
    return client_cls(
        include_paths=set(app.config.get('SENTRY_INCLUDE_PATHS', [])) | set([app.import_name]),
        exclude_paths=app.config.get('SENTRY_EXCLUDE_PATHS'),
        servers=app.config.get('SENTRY_SERVERS'),
        name=app.config.get('SENTRY_NAME'),
        key=app.config.get('SENTRY_KEY'),
        public_key=app.config.get('SENTRY_PUBLIC_KEY'),
        secret_key=app.config.get('SENTRY_SECRET_KEY'),
        project=app.config.get('SENTRY_PROJECT'),
        site=app.config.get('SENTRY_SITE_NAME'),
        dsn=dsn or app.config.get('SENTRY_DSN') or os.environ.get('SENTRY_DSN'),
    )


class Sentry(object):
    """
    Flask application for Sentry.

    Look up configuration from ``os.environ['SENTRY_DSN']``::

    >>> sentry = Sentry(app)

    Pass an arbitrary DSN::

    >>> sentry = Sentry(app, dsn='http://public:secret@example.com/1')

    Pass an explicit client::

    >>> sentry = Sentry(app, client=client)

    Automatically configure logging::

    >>> sentry = Sentry(app, logging=True)

    Capture an exception::

    >>> try:
    >>>     1 / 0
    >>> except ZeroDivisionError:
    >>>     sentry.captureException()

    Capture a message::

    >>> sentry.captureMessage('hello, world!')
    """
    def __init__(self, app=None, client=None, client_cls=Client, dsn=None,
                 logging=False):
        self.dsn = dsn
        self.logging = logging
        self.client_cls = client_cls
        self.client = client

        if app:
            self.init_app(app)

    def handle_exception(self, *args, **kwargs):
        if not self.client:
            return

        self.client.capture('Exception', exc_info=kwargs.get('exc_info'),
            data=get_data_from_request(request),
            extra={
                'app': self.app,
            },
        )

    def init_app(self, app):
        self.app = app
        if not self.client:
            self.client = make_client(self.client_cls, app, self.dsn)

        if self.logging:
            setup_logging(SentryHandler(self.client))

        got_request_exception.connect(self.handle_exception, sender=app)

    def captureException(self, *args, **kwargs):
        assert self.client, 'captureException called before application configured'
        return self.client.captureException(*args, **kwargs)

    def captureMessage(self, *args, **kwargs):
        assert self.client, 'captureMessage called before application configured'
        return self.client.captureMessage(*args, **kwargs)
