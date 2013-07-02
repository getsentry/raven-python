"""
raven.transport.builtins
~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import logging
import sys
from raven.utils import compat

try:
    # Google App Engine blacklists parts of the socket module, this will prevent
    # it from blowing up.
    from socket import socket, AF_INET, SOCK_DGRAM, error as socket_error
    has_socket = True
except:
    has_socket = False

try:
    import gevent
    # gevent 1.0bN renamed coros to lock
    try:
        from gevent.lock import Semaphore
    except ImportError:
        from gevent.coros import Semaphore  # NOQA
    has_gevent = True
except:
    has_gevent = None

try:
    import twisted.web.client
    import twisted.internet.protocol
    has_twisted = True
except:
    has_twisted = False

try:
    from tornado import ioloop
    from tornado.httpclient import AsyncHTTPClient, HTTPClient
    has_tornado = True
except:
    has_tornado = False

try:
    import eventlet
    from eventlet.green import urllib2 as eventlet_urllib2
    has_eventlet = True
except:
    has_eventlet = False

from raven.conf import defaults
from raven.transport.exceptions import InvalidScheme


class Transport(object):
    """
    All transport implementations need to subclass this class

    You must implement a send method (or an async_send method if
    sub-classing AsyncTransport) and the compute_scope method.

    Please see the HTTPTransport class for an example of a
    compute_scope implementation.
    """

    async = False

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
        raise NotImplementedError


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


class BaseUDPTransport(Transport):
    def __init__(self, parsed_url):
        super(BaseUDPTransport, self).__init__()
        self.check_scheme(parsed_url)
        self._parsed_url = parsed_url

    def send(self, data, headers):
        auth_header = headers.get('X-Sentry-Auth')

        if auth_header is None:
            # silently ignore attempts to send messages without an auth header
            return

        host, port = self._parsed_url.netloc.split(':')
        self._send_data(auth_header + '\n\n' + data, (host, int(port)))

    def compute_scope(self, url, scope):
        path_bits = url.path.rsplit('/', 1)
        if len(path_bits) > 1:
            path = path_bits[0]
        else:
            path = ''
        project = path_bits[-1]

        if not all([url.port, project, url.username, url.password]):
            raise ValueError('Invalid Sentry DSN: %r' % url.geturl())

        netloc = url.hostname
        netloc += ':%s' % url.port

        server = '%s://%s%s/api/%s/store/' % (
            url.scheme, netloc, path, project)
        scope.update({
            'SENTRY_SERVERS': [server],
            'SENTRY_PROJECT': project,
            'SENTRY_PUBLIC_KEY': url.username,
            'SENTRY_SECRET_KEY': url.password,
        })
        return scope


class UDPTransport(BaseUDPTransport):
    scheme = ['udp']

    def __init__(self, parsed_url):
        super(UDPTransport, self).__init__(parsed_url)
        if not has_socket:
            raise ImportError('UDPTransport requires the socket module')

    def _send_data(self, data, addr):
        udp_socket = None
        try:
            udp_socket = socket(AF_INET, SOCK_DGRAM)
            udp_socket.setblocking(False)
            udp_socket.sendto(data, addr)
        except socket_error:
            # as far as I understand things this simply can't happen,
            # but still, it can't hurt
            pass
        finally:
            # Always close up the socket when we're done
            if udp_socket is not None:
                udp_socket.close()
                udp_socket = None


class HTTPTransport(Transport):

    scheme = ['http', 'https']

    def __init__(self, parsed_url, timeout=defaults.TIMEOUT):
        self.check_scheme(parsed_url)

        self._parsed_url = parsed_url
        self._url = parsed_url.geturl()
        self.timeout = timeout

    def send(self, data, headers):
        """
        Sends a request to a remote webserver using HTTP POST.
        """
        req = compat.Request(self._url, headers=headers)

        if sys.version_info < (2, 6):
            response = compat.urlopen(req, data).read()
        else:
            response = compat.urlopen(req, data, self.timeout).read()
        return response

    def compute_scope(self, url, scope):
        netloc = url.hostname
        if url.port and (url.scheme, url.port) not in \
                (('http', 80), ('https', 443)):
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
        })
        return scope


class GeventedHTTPTransport(AsyncTransport, HTTPTransport):

    scheme = ['gevent+http', 'gevent+https']

    def __init__(self, parsed_url, maximum_outstanding_requests=100):
        if not has_gevent:
            raise ImportError('GeventedHTTPTransport requires gevent.')
        self._lock = Semaphore(maximum_outstanding_requests)

        super(GeventedHTTPTransport, self).__init__(parsed_url)

        # remove the gevent+ from the protocol, as it is not a real protocol
        self._url = self._url.split('+', 1)[-1]

    def async_send(self, data, headers, success_cb, failure_cb):
        """
        Spawn an async request to a remote webserver.
        """
        # this can be optimized by making a custom self.send that does not
        # read the response since we don't use it.
        self._lock.acquire()
        return gevent.spawn(
            super(GeventedHTTPTransport, self).send, data, headers
        ).link(lambda x: self._done(x, success_cb, failure_cb))

    def _done(self, greenlet, success_cb, failure_cb, *args):
        self._lock.release()
        if greenlet.successful():
            success_cb()
        else:
            failure_cb(greenlet.value)


class TwistedHTTPTransport(AsyncTransport, HTTPTransport):

    scheme = ['twisted+http', 'twisted+https']

    def __init__(self, parsed_url):
        if not has_twisted:
            raise ImportError('TwistedHTTPTransport requires twisted.web.')

        super(TwistedHTTPTransport, self).__init__(parsed_url)
        self.logger = logging.getLogger('sentry.errors')

        # remove the twisted+ from the protocol, as it is not a real protocol
        self._url = self._url.split('+', 1)[-1]

    def async_send(self, data, headers, success_cb, failure_cb):
        d = twisted.web.client.getPage(self._url, method='POST', postdata=data,
                                       headers=headers)
        d.addCallback(lambda r: success_cb())
        d.addErrback(lambda f: failure_cb(f.value))


class TwistedUDPTransport(BaseUDPTransport):
    scheme = ['twisted+udp']

    def __init__(self, parsed_url):
        super(TwistedUDPTransport, self).__init__(parsed_url)
        if not has_twisted:
            raise ImportError('TwistedUDPTransport requires twisted.')
        self.protocol = twisted.internet.protocol.DatagramProtocol()
        twisted.internet.reactor.listenUDP(0, self.protocol)

    def _send_data(self, data, addr):
        self.protocol.transport.write(data, addr)


class TornadoHTTPTransport(HTTPTransport):

    scheme = ['tornado+http']

    def __init__(self, parsed_url):
        if not has_tornado:
            raise ImportError('TornadoHTTPTransport requires tornado.')

        super(TornadoHTTPTransport, self).__init__(parsed_url)

        # remove the tornado+ from the protocol, as it is not a real protocol
        self._url = self._url.split('+', 1)[-1]

    def send(self, data, headers):
        kwargs = dict(method='POST', headers=headers, body=data)

        # only use async if ioloop is running, otherwise it will never send
        if ioloop.IOLoop.initialized():
            client = AsyncHTTPClient()
            kwargs['callback'] = None
        else:
            client = HTTPClient()

        client.fetch(self._url, **kwargs)


class EventletHTTPTransport(HTTPTransport):

    scheme = ['eventlet+http', 'eventlet+https']

    def __init__(self, parsed_url, pool_size=100):
        if not has_eventlet:
            raise ImportError('EventletHTTPTransport requires eventlet.')
        super(EventletHTTPTransport, self).__init__(parsed_url)
        # remove the eventlet+ from the protocol, as it is not a real protocol
        self._url = self._url.split('+', 1)[-1]

    def _send_payload(self, payload):
        req = eventlet_urllib2.Request(self._url, headers=payload[1])
        try:
            if sys.version_info < (2, 6):
                response = eventlet_urllib2.urlopen(req, payload[0]).read()
            else:
                response = eventlet_urllib2.urlopen(req, payload[0],
                                                    self.timeout).read()
            return response
        except Exception as err:
            return err

    def send(self, data, headers):
        """
        Spawn an async request to a remote webserver.
        """
        eventlet.spawn(self._send_payload, (data, headers))
