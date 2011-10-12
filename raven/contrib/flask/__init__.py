"""
raven.contrib.flask
~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

from flask import request
from flask.signals import got_request_exception
from raven.base import Client

class Sentry(object):

    def __init__(self, app=None, client=None, client_cls=Client):
        self.app = app
        self.client = client
        self.client_cls = client_cls

        if app:
            self.init_app(app)

    def handle_exception(self, client):
        def _handle_exception(sender, **kwargs):
            client.create_from_exception(
                exc_info=kwargs.get('exc_info'),
                url=request.url,
                data={
                    'META': request.environ,
                    'GET': request.args,
                    'POST': request.form,
                    'app': sender.name,
                },
            )
        return _handle_exception

    def init_app(self, app):
        if not self.client:
            if not app.config.get('SENTRY_SERVERS'):
                raise TypeError('The SENTRY_SERVERS config variable is required.')
            if not app.config.get('SENTRY_KEY'):
                raise TypeError('The SENTRY_KEY config variable is required.')
            client = self.client_cls(
                include_paths=set(app.config.get('SENTRY_INCLUDE_PATHS', [])) | set([app.import_name]),
                exclude_paths=app.config.get('SENTRY_EXCLUDE_PATHS'),
                servers=app.config.get('SENTRY_SERVERS'),
                name=app.config.get('SENTRY_NAME'),
                key=app.config.get('SENTRY_KEY'),
            )
        else:
            client = self.client

        got_request_exception.connect(self.handle_exception(client), sender=app, weak=False)
