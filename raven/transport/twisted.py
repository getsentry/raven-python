"""
raven.transport.twisted
~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import logging

from raven.transport.base import AsyncTransport
from raven.transport.http import HTTPTransport
from raven.transport.udp import BaseUDPTransport

try:
    import twisted.web.client
    import twisted.internet.protocol
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
