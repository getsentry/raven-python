"""
raven.transport.asyncio
~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2014 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import logging

from raven.transport.base import AsyncTransport
from raven.transport.http import HTTPTransport
from raven.transport.udp import BaseUDPTransport

try:
    import asyncio
    import aiohttp
    has_asyncio = True
except:
    has_asyncio = False


class AsyncioHttpTransport(AsyncTransport, HTTPTransport):

    scheme = ['asyncio+http', 'asyncio+https']

    def __init__(self, parsed_url, *, loop=None):
        if not has_asyncio:
            raise ImportError('AIOHttpTransport requires asyncio and aiohttp.')

        if loop is None:
            loop = asyncio.get_event_loop()
        self._loop = loop

        super().__init__(parsed_url)
        self.logger = logging.getLogger('sentry.errors')

        # remove the aiohttp+ from the protocol, as it is not a real protocol
        self._url = self._url.split('+', 1)[-1]

    def async_send(self, data, headers, success_cb, failure_cb):
        @asyncio.coroutine
        def f():
            try:
                resp = yield from aiohttp.request('POST',
                                                  self._url, data=data,
                                                  headers=headers,
                                                  loop=self._loop)
                resp.close()
                success_cb()
            except Exception as exc:
                failure_cb(exc)
        asyncio.async(f(), loop=self._loop)


class AsyncioUDPTransport(BaseUDPTransport):
    scheme = ['asyncio+udp']

    def __init__(self, parsed_url, *, loop=None):
        super().__init__(parsed_url)
        if not has_asyncio:
            raise ImportError('AsyncioUDPTransport requires asyncio.')
        if loop is None:
            loop = asyncio.get_event_loop()
        self._loop = loop

        self._transport, _ = loop.run_until_complete(
            loop.create_datagram_endpoint(asyncio.DatagramProtocol))

    def _send_data(self, data, addr):
        self._transport.send_to(data, addr)
