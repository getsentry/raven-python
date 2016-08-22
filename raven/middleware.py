"""
raven.middleware
~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from raven._compat import Iterator, next
from raven.utils.wsgi import (
    get_current_url, get_headers, get_environ)


class ClosingIterator(Iterator):
    """
    An iterator that is implements a ``close`` method as-per
    WSGI recommendation.
    """
    def __init__(self, sentry, iterable, environ):
        self.sentry = sentry
        self.environ = environ
        self.iterable = iter(iterable)

    def __iter__(self):
        return self

    def __next__(self):
        try:
            return next(self.iterable)
        except StopIteration:
            # propagate up the normal StopIteration
            raise
        except Exception:
            # but capture any other exception, then re-raise
            self.sentry.handle_exception(self.environ)
            raise
        except KeyboardInterrupt:
            self.sentry.handle_exception(self.environ)
            raise
        except SystemExit as e:
            if e.code != 0:
                self.sentry.handle_exception(self.environ)
            raise

    def close(self):
        if hasattr(self.iterable, 'close') and callable(self.iterable.close):
            try:
                self.iterable.close()
            except Exception:
                self.sentry.handle_exception(self.environ)
            except KeyboardInterrupt:
                self.sentry.handle_exception(self.environ)
                raise
            except SystemExit as e:
                if e.code != 0:
                    self.sentry.handle_exception(self.environ)
                raise
            self.sentry.client.context.clear()


class Sentry(object):
    """
    A WSGI middleware which will attempt to capture any
    uncaught exceptions and send them to Sentry.

    >>> from raven.base import Client
    >>> application = Sentry(application, Client())
    """
    def __init__(self, application, client=None):
        self.application = application
        if client is None:
            from raven.base import Client
            client = Client()
        self.client = client

    def __call__(self, environ, start_response):
        # TODO(dcramer): ideally this is lazy, but the context helpers must
        # support callbacks first
        self.client.http_context(self.get_http_context(environ))

        try:
            iterable = self.application(environ, start_response)
        except Exception:
            self.handle_exception(environ)
            raise
        except KeyboardInterrupt:
            self.handle_exception(environ)
            raise
        except SystemExit as e:
            if e.code != 0:
                self.handle_exception(environ)
            raise

        return ClosingIterator(self, iterable, environ)

    def get_http_context(self, environ):
        return {
            'method': environ.get('REQUEST_METHOD'),
            'url': get_current_url(environ, strip_querystring=True),
            'query_string': environ.get('QUERY_STRING'),
            # TODO
            # 'data': environ.get('wsgi.input'),
            'headers': dict(get_headers(environ)),
            'env': dict(get_environ(environ)),
        }

    def process_response(self, request, response):
        self.client.context.clear()

    def handle_exception(self, environ=None):
        return self.client.captureException()
