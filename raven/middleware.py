"""
raven.middleware
~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from raven.utils.wsgi import (
    get_current_url, get_headers, get_environ)


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

        try:
            for event in iterable:
                yield event
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
        finally:
            # wsgi spec requires iterable to call close if it exists
            # see http://blog.dscpl.com.au/2012/10/obligations-for-calling-close-on.html
            if iterable and hasattr(iterable, 'close') and callable(iterable.close):
                try:
                    iterable.close()
                except Exception:
                    self.handle_exception(environ)
                except KeyboardInterrupt:
                    self.handle_exception(environ)
                    raise
                except SystemExit as e:
                    if e.code != 0:
                        self.handle_exception(environ)
                    raise
            self.client.context.clear()

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
