"""
raven.transport.base
~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from raven.transport.exceptions import InvalidScheme
from raven.utils.compat import urlparse


class Transport(object):
    """
    All transport implementations need to subclass this class

    You must implement a send method (or an async_send method if
    sub-classing AsyncTransport) and the compute_scope method.

    Please see the HTTPTransport class for an example of a
    compute_scope implementation.
    """

    async = False
    scheme = []

    def check_scheme(self, url):
        if url.scheme not in self.scheme:
            raise InvalidScheme()

    def send(self, data, headers):
        """
        You need to override this to do something with the actual
        data. Usually - this is sending to a server
        """
        raise NotImplementedError

    def compute_scope(self, url, scope):
        """
        You need to override this to compute the SENTRY specific
        additions to the variable scope.  See the HTTPTransport for an
        example.
        """
        netloc = url.hostname
        if url.port:
            netloc += ':%s' % url.port

        path_bits = url.path.rsplit('/', 1)
        if len(path_bits) > 1:
            path = path_bits[0]
        else:
            path = ''
        project = path_bits[-1]

        if not all([netloc, project, url.username, url.password]):
            raise ValueError('Invalid Sentry DSN: %r' % url.geturl())

        server = '%s://%s%s/api/%s/store/' % (
            url.scheme, netloc, path, project)

        scope.update({
            'SENTRY_SERVERS': [server],
            'SENTRY_PROJECT': project,
            'SENTRY_PUBLIC_KEY': url.username,
            'SENTRY_SECRET_KEY': url.password,
            'SENTRY_TRANSPORT_OPTIONS': dict(urlparse.parse_qsl(url.query)),
        })
        return scope


class AsyncTransport(Transport):
    """
    All asynchronous transport implementations should subclass this
    class.

    You must implement a async_send method (and the compute_scope
    method as describe on the base Transport class).
    """

    async = True

    def async_send(self, data, headers, success_cb, error_cb):
        """
        Override this method for asynchronous transports. Call
        `success_cb()` if the send succeeds or `error_cb(exception)`
        if the send fails.
        """
        raise NotImplementedError
