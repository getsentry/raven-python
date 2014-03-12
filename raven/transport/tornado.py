"""
raven.transport.tornado
~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from raven.transport.http import HTTPTransport

try:
    from tornado import ioloop
    from tornado.httpclient import AsyncHTTPClient, HTTPClient
    has_tornado = True
except:
    has_tornado = False


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
