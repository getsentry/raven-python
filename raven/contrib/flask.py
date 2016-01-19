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

from flask import request, current_app, g
from flask.signals import got_request_exception, request_finished
from werkzeug.exceptions import ClientDisconnected

from raven._compat import string_types
from raven.conf import setup_logging
from raven.base import Client
from raven.middleware import Sentry as SentryMiddleware
from raven.handlers.logging import SentryHandler
from raven.utils.compat import _urlparse
from raven.utils.encoding import to_unicode
from raven.utils.imports import import_string
from raven.utils.wsgi import get_headers, get_environ


def make_client(client_cls, app, dsn=None):
    # TODO(dcramer): django and Flask share very similar concepts here, and
    # should be refactored
    transport = app.config.get('SENTRY_TRANSPORT')
    if isinstance(transport, string_types):
        transport = import_string(transport)

    return client_cls(
        dsn=dsn or app.config.get('SENTRY_DSN') or os.environ.get('SENTRY_DSN'),
        transport=transport,
        include_paths=set(app.config.get(
            'SENTRY_INCLUDE_PATHS', [])) | set([app.import_name]),
        exclude_paths=app.config.get('SENTRY_EXCLUDE_PATHS'),
        name=app.config.get('SENTRY_NAME'),
        site=app.config.get('SENTRY_SITE_NAME'),
        processors=app.config.get('SENTRY_PROCESSORS'),
        string_max_length=app.config.get('SENTRY_MAX_LENGTH_STRING'),
        list_max_length=app.config.get('SENTRY_MAX_LENGTH_LIST'),
        auto_log_stacks=app.config.get('SENTRY_AUTO_LOG_STACKS'),
        tags=app.config.get('SENTRY_TAGS'),
        release=app.config.get('SENTRY_RELEASE'),
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
    # TODO(dcramer): the client isn't using local context and therefore
    # gets shared by every app that does init on it
    def __init__(self, app=None, client=None, client_cls=Client, dsn=None,
                 logging=False, logging_exclusions=None, level=logging.NOTSET,
                 wrap_wsgi=None, register_signal=True):
        self.dsn = dsn
        self.logging = logging
        self.logging_exclusions = logging_exclusions
        self.client_cls = client_cls
        self.client = client
        self.level = level
        self.wrap_wsgi = wrap_wsgi
        self.register_signal = register_signal

        if app:
            self.init_app(app)

    @property
    def last_event_id(self):
        return getattr(self, '_last_event_id', None)

    @last_event_id.setter
    def last_event_id(self, value):
        self._last_event_id = value
        try:
            g.sentry_event_id = value
        except Exception:
            pass

    def handle_exception(self, *args, **kwargs):
        if not self.client:
            return

        ignored_exc_type_list = current_app.config.get(
            'RAVEN_IGNORE_EXCEPTIONS', [])
        exc = sys.exc_info()[1]

        if any((isinstance(exc, ignored_exc_type)
                for ignored_exc_type in ignored_exc_type_list)):
            return

        self.captureException(exc_info=kwargs.get('exc_info'))

    def get_user_info(self, request):
        """
        Requires Flask-Login (https://pypi.python.org/pypi/Flask-Login/)
        to be installed
        and setup
        """
        if not has_flask_login:
            return

        if not hasattr(current_app, 'login_manager'):
            return

        try:
            is_authenticated = current_user.is_authenticated
        except AttributeError:
            # HACK: catch the attribute error thrown by flask-login is not attached
            # >   current_user = LocalProxy(lambda: _request_ctx_stack.top.user)
            # E   AttributeError: 'RequestContext' object has no attribute 'user'
            return {}

        if callable(is_authenticated):
            is_authenticated = is_authenticated()

        if not is_authenticated:
            return {}

        user_info = {
            'id': current_user.get_id(),
        }

        if 'SENTRY_USER_ATTRS' in current_app.config:
            for attr in current_app.config['SENTRY_USER_ATTRS']:
                if hasattr(current_user, attr):
                    user_info[attr] = getattr(current_user, attr)

        return user_info

    def get_http_info(self, request):
        """
        Determine how to retrieve actual data by using request.mimetype.
        """
        if self.is_json_type(request.mimetype):
            retriever = self.get_json_data
        else:
            retriever = self.get_form_data
        return self.get_http_info_with_retriever(request, retriever)

    def is_json_type(self, content_type):
        return content_type == 'application/json'

    def get_form_data(self, request):
        return request.form

    def get_json_data(self, request):
        return request.data

    def get_http_info_with_retriever(self, request, retriever=None):
        """
        Exact method for getting http_info but with form data work around.
        """
        if retriever is None:
            retriever = self.get_form_data

        urlparts = _urlparse.urlsplit(request.url)

        try:
            data = retriever(request)
        except ClientDisconnected:
            data = {}

        return {
            'url': '%s://%s%s' % (urlparts.scheme, urlparts.netloc, urlparts.path),
            'query_string': urlparts.query,
            'method': request.method,
            'data': data,
            'headers': dict(get_headers(request.environ)),
            'env': dict(get_environ(request.environ)),
        }

    def before_request(self, *args, **kwargs):
        self.last_event_id = None
        try:
            self.client.http_context(self.get_http_info(request))
        except Exception as e:
            self.client.logger.exception(to_unicode(e))
        try:
            self.client.user_context(self.get_user_info(request))
        except Exception as e:
            self.client.logger.exception(to_unicode(e))

    def after_request(self, sender, response, *args, **kwargs):
        if self.last_event_id:
            response.headers['X-Sentry-ID'] = self.last_event_id
        self.client.context.clear()
        return response

    def init_app(self, app, dsn=None, logging=None, level=None,
                 logging_exclusions=None, wrap_wsgi=None,
                 register_signal=None):
        if dsn is not None:
            self.dsn = dsn

        if level is not None:
            self.level = level

        if wrap_wsgi is not None:
            self.wrap_wsgi = wrap_wsgi
        elif self.wrap_wsgi is None:
            # Fix https://github.com/getsentry/raven-python/issues/412
            # the gist is that we get errors twice in debug mode if we don't do this
            if app and app.debug:
                self.wrap_wsgi = False
            else:
                self.wrap_wsgi = True

        if register_signal is not None:
            self.register_signal = register_signal

        if logging is not None:
            self.logging = logging

        if logging_exclusions is not None:
            self.logging_exclusions = logging_exclusions

        if not self.client:
            self.client = make_client(self.client_cls, app, self.dsn)

        if self.logging:
            kwargs = {}
            if self.logging_exclusions is not None:
                kwargs['exclude'] = self.logging_exclusions

            setup_logging(SentryHandler(self.client, level=self.level), **kwargs)

        if self.wrap_wsgi:
            app.wsgi_app = SentryMiddleware(app.wsgi_app, self.client)

        app.before_request(self.before_request)

        if self.register_signal:
            got_request_exception.connect(self.handle_exception, sender=app)
            request_finished.connect(self.after_request, sender=app)

        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['sentry'] = self

    def captureException(self, *args, **kwargs):
        assert self.client, 'captureException called before application configured'
        result = self.client.captureException(*args, **kwargs)
        if result:
            self.last_event_id = self.client.get_ident(result)
        else:
            self.last_event_id = None
        return result

    def captureMessage(self, *args, **kwargs):
        assert self.client, 'captureMessage called before application configured'
        result = self.client.captureMessage(*args, **kwargs)
        if result:
            self.last_event_id = self.client.get_ident(result)
        else:
            self.last_event_id = None
        return result

    def user_context(self, *args, **kwargs):
        assert self.client, 'user_context called before application configured'
        return self.client.user_context(*args, **kwargs)

    def tags_context(self, *args, **kwargs):
        assert self.client, 'tags_context called before application configured'
        return self.client.tags_context(*args, **kwargs)

    def extra_context(self, *args, **kwargs):
        assert self.client, 'extra_context called before application configured'
        return self.client.extra_context(*args, **kwargs)
