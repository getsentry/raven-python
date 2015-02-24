"""
raven.transport.twisted
~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import io
import logging

from raven.transport.base import AsyncTransport
from raven.transport.http import HTTPTransport
from raven.transport.udp import BaseUDPTransport

try:
    import twisted.internet.protocol
    from twisted.web.client import (
        Agent, FileBodyProducer, HTTPConnectionPool, ResponseNeverReceived,
        readBody,
    )
    from twisted.web.http_headers import Headers
    has_twisted = True
except:
    has_twisted = False


class TwistedHTTPTransport(AsyncTransport, HTTPTransport):

    scheme = ['twisted+http', 'twisted+https']

    def __init__(self, parsed_url):
        if not has_twisted:
            raise ImportError('TwistedHTTPTransport requires twisted.web.')

        super(TwistedHTTPTransport, self).__init__(parsed_url)
        self.logger = logging.getLogger('sentry.errors')

        # remove the twisted+ from the protocol, as it is not a real protocol
        self._url = self._url.split('+', 1)[-1]

        # Import reactor as late as possible.
        from twisted.internet import reactor

        # Use a persistent connection pool.
        self._agent = Agent(reactor, pool=HTTPConnectionPool(reactor))

    def async_send(self, data, headers, success_cb, failure_cb):
        d = self._agent.request(
            b"POST", self._url,
            bodyProducer=FileBodyProducer(io.BytesIO(data)),
            headers=Headers(dict((k, [v]) for k, v in headers.items()))
        )

        def on_failure(failure):
            ex = failure.check(ResponseNeverReceived)
            if ex:
                # ResponseNeverReceived wraps the actual error(s).
                failure_cb([f.value for f in failure.value.reasons])
            else:
                failure_cb(failure.value)

        def on_success(response):
            """
            Success only means that the request succeeded, *not* that the
            actual submission was successful.
            """
            if response.code == 200:
                success_cb()
            else:
                def on_error_body(body):
                    failure_cb(Exception(response.code, response.phrase, body))

                return readBody(response).addCallback(
                    on_error_body,
                )

        d.addCallback(
            on_success,
        ).addErrback(
            on_failure,
        )


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
