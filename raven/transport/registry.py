"""
raven.transport.registry
~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from raven.transport.base import (
    HTTPTransport, GeventedHTTPTransport, TwistedHTTPTransport,
    TornadoHTTPTransport, UDPTransport, EventletHTTPTransport)
from raven.transport.exceptions import DuplicateScheme
from raven.transport.threaded import ThreadedHTTPTransport
from raven.utils import urlparse


class TransportRegistry(object):
    def __init__(self, transports=None):
        # setup a default list of senders
        self._schemes = {}
        self._transports = {}

        if transports:
            for transport in transports:
                self.register_transport(transport)

    def register_transport(self, transport):
        if not hasattr(transport, 'scheme') or not hasattr(transport.scheme, '__iter__'):
            raise AttributeError('Transport %s must have a scheme list', transport.__class__.__name__)

        for scheme in transport.scheme:
            self.register_scheme(scheme, transport)

    def register_scheme(self, scheme, cls):
        """
        It is possible to inject new schemes at runtime
        """
        if scheme in self._schemes:
            raise DuplicateScheme()

        urlparse.register_scheme(scheme)
        # TODO (vng): verify the interface of the new class
        self._schemes[scheme] = cls

    def supported_scheme(self, scheme):
        return scheme in self._schemes

    def get_transport(self, parsed_url):
        full_url = parsed_url.geturl()
        if full_url not in self._transports:
            # Grab options from the querystring to pass to the transport
            # e.g. ?timeout=30
            if parsed_url.query:
                options = dict(q.split('=', 1) for q in parsed_url.query.split('&'))
            else:
                options = dict()
            self._transports[full_url] = self._schemes[parsed_url.scheme](parsed_url, **options)
        return self._transports[full_url]

    def compute_scope(self, url, scope):
        """
        Compute a scope dictionary.  This may be overridden by custom
        transports
        """
        transport = self._schemes[url.scheme](url)
        return transport.compute_scope(url, scope)


default_transports = [
    HTTPTransport,
    ThreadedHTTPTransport,
    GeventedHTTPTransport,
    TwistedHTTPTransport,
    TornadoHTTPTransport,
    UDPTransport,
    EventletHTTPTransport,
]
