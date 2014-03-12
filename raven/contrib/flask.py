"""
raven.contrib.flask
~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

try:
    from flask_login import current_user
except ImportError:
    has_flask_login = False
else:
    has_flask_login = True

import sys
import os
import logging

from flask import request, current_app
from flask.signals import got_request_exception
from raven.conf import setup_logging
from raven.base import Client
from raven.middleware import Sentry as SentryMiddleware
from raven.handlers.logging import SentryHandler
from raven.utils.compat import _urlparse
from raven.utils.wsgi import get_headers, get_environ
from werkzeug.exceptions import ClientDisconnected


def make_client(client_cls, app, dsn=None):
    return client_cls(
        dsn=dsn or app.config.get('SENTRY_DSN') or os.environ.get('SENTRY_DSN'),
        include_paths=set(app.config.get('SENTRY_INCLUDE_PATHS', [])) | set([app.import_name]),
        exclude_paths=app.config.get('SENTRY_EXCLUDE_PATHS'),
        servers=app.config.get('SENTRY_SERVERS'),
        name=app.config.get('SENTRY_NAME'),
        public_key=app.config.get('SENTRY_PUBLIC_KEY'),
        secret_key=app.config.get('SENTRY_SECRET_KEY'),
        project=app.config.get('SENTRY_PROJECT'),
        site=app.config.get('SENTRY_SITE_NAME'),
        processors=app.config.get('SENTRY_PROCESSORS'),
        string_max_length=app.config.get('SENTRY_MAX_LENGTH_STRING'),
        list_max_length=app.config.get('SENTRY_MAX_LENGTH_LIST'),
        extra={
            'app': app,
        },
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

    >>> sentry = Sentry(app, logging=True, level=logging.ERROR)

    Capture an exception::

    >>> try:
    >>>     1 / 0
    >>> except ZeroDivisionError:
    >>>     sentry.captureException()

    Capture a message::

    >>> sentry.captureMessage('hello, world!')

    By default, the Flask integration will do the following:

    - Hook into the `got_request_exception` signal. This can be disabled by
      passing `register_signal=False`.
    - Wrap the WSGI application. This can be disabled by passing
      `wrap_wsgi=False`.
    - Capture information from Flask-Login (if available).
    """
    def __init__(self, app=None, client=None, client_cls=Client, dsn=None,
                 logging=False, level=logging.NOTSET, wrap_wsgi=True,
                 register_signal=True):
        self.dsn = dsn
        self.logging = logging
        self.client_cls = client_cls
        self.client = client
        self.level = level
        self.wrap_wsgi = wrap_wsgi
        self.register_signal = register_signal

        if app:
            self.init_app(app)

    def handle_exception(self, *args, **kwargs):
        if not self.client:
            return

        ignored_exc_type_list = current_app.config.get('RAVEN_IGNORE_EXCEPTIONS', [])
        exc = sys.exc_info()[1]

        if any((isinstance(exc, ignored_exc_type) for ignored_exc_type in ignored_exc_type_list)):
            return

        self.captureException(exc_info=kwargs.get('exc_info'))

    def get_user_info(self, request):
        """
        Requires Flask-Login (https://pypi.python.org/pypi/Flask-Login/) to be installed
        and setup
        """
        if not has_flask_login:
            return

        if not hasattr(current_app, 'login_manager'):
            return

        try:
            is_authenticated = current_user.is_authenticated()
        except AttributeError:
            # HACK: catch the attribute error thrown by flask-login is not attached
            # >   current_user = LocalProxy(lambda: _request_ctx_stack.top.user)
            # E   AttributeError: 'RequestContext' object has no attribute 'user'
            return {}

        if is_authenticated:
            user_info = {
                'is_authenticated': True,
                'is_anonymous': current_user.is_anonymous(),
                'id': current_user.get_id(),
            }

            if 'SENTRY_USER_ATTRS' in current_app.config:
                for attr in current_app.config['SENTRY_USER_ATTRS']:
                    if hasattr(current_user, attr):
                        user_info[attr] = getattr(current_user, attr)
        else:
            user_info = {
                'is_authenticated': False,
                'is_anonymous': current_user.is_anonymous(),
            }

        return user_info

    def get_http_info(self, request):
        urlparts = _urlparse.urlsplit(request.url)

        try:
            formdata = request.form
        except ClientDisconnected:
            formdata = {}

        return {
            'url': '%s://%s%s' % (urlparts.scheme, urlparts.netloc, urlparts.path),
            'query_string': urlparts.query,
            'method': request.method,
            'data': formdata,
            'headers': dict(get_headers(request.environ)),
            'env': dict(get_environ(request.environ)),
        }

    def before_request(self, *args, **kwargs):
        self.client.http_context(self.get_http_info(request))
        self.client.user_context(self.get_user_info(request))

    def init_app(self, app, dsn=None):
        if dsn is not None:
            self.dsn = dsn

        if not self.client:
            self.client = make_client(self.client_cls, app, self.dsn)

        if self.logging:
            setup_logging(SentryHandler(self.client, level=self.level))

        if self.wrap_wsgi:
            app.wsgi_app = SentryMiddleware(app.wsgi_app, self.client)

        app.before_request(self.before_request)

        if self.register_signal:
            got_request_exception.connect(self.handle_exception, sender=app)

        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['sentry'] = self

    def captureException(self, *args, **kwargs):
        assert self.client, 'captureException called before application configured'
        return self.client.captureException(*args, **kwargs)

    def captureMessage(self, *args, **kwargs):
        assert self.client, 'captureMessage called before application configured'
        return self.client.captureMessage(*args, **kwargs)
