"""
raven.transport.aiohttp
~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2014 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
# Skip flake8, python2 version doesn't recognize `yield from` statement
# flake8: noqa
from __future__ import absolute_import

from raven.transport.base import AsyncTransport
from raven.transport.http import HTTPTransport

try:
    import aiohttp
    import asyncio
    has_aiohttp = True
except:
    has_aiohttp = False


class AioHttpTransport(AsyncTransport, HTTPTransport):

    scheme = ['aiohttp+http', 'aiohttp+https']

    def __init__(self, parsed_url, *, loop=None):
        if not has_aiohttp:
            raise ImportError('AioHttpTransport requires asyncio and aiohttp.')

        if loop is None:
            loop = asyncio.get_event_loop()
        self._loop = loop

        super().__init__(parsed_url)

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
