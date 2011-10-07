"""
raven.contrib.flask
~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

from flask import request
from raven.base import Client

class Sentry(object):
    def __init__(self, app=None, client=None, client_cls=Client):
        self.app = app
        self.client = client
        self.client_cls = client_cls
        if app:
            self.init_app(app)

    def init_app(self, app):
        self.app = app
        app.error_handler_spec[None][500] = self.handle_exception
        if not self.client:
            self.client = self.client_cls(
                include_paths=app.config.get('SENTRY_INCLUDE_PATHS'),
                exclude_paths=app.config.get('SENTRY_EXCLUDE_PATHS'),
                remote_urls=app.config.get('SENTRY_REMOTE_URLS'),
                name=app.config.get('SENTRY_NAME'),
                key=app.config.get('SENTRY_KEY'),
            )

    def handle_exception(self, error):
        if not self.client:
            return

        event_id = self.client.create_from_exception(
            url=request.url,
            data={
                'META': request.environ,
                'GET': request.args,
                'POST': request.form,
            },
        )
        # TODO: this should be handled by the parent application
        return 'An unknown error occurred', 500
