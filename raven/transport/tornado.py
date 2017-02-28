"""
raven.transport.tornado
~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from functools import partial

from raven.transport.base import AsyncTransport
from raven.transport.http import HTTPTransport

try:
    from tornado import ioloop
    from tornado.httpclient import AsyncHTTPClient, HTTPClient
    has_tornado = True
except:
    has_tornado = False


class TornadoHTTPTransport(AsyncTransport, HTTPTransport):

    scheme = ['tornado+http', 'tornado+https']

    def __init__(self, parsed_url, *args, **kwargs):
        if not has_tornado:
            raise ImportError('TornadoHTTPTransport requires tornado.')

        super(TornadoHTTPTransport, self).__init__(parsed_url, *args, **kwargs)

    def async_send(self, data, headers, success_cb, failure_cb):
        kwargs = dict(method='POST', headers=headers, body=data)
        kwargs["validate_cert"] = self.verify_ssl
        kwargs["connect_timeout"] = self.timeout
        kwargs["ca_certs"] = self.ca_certs

        # only use async if ioloop is running, otherwise it will never send
        if ioloop.IOLoop.initialized():
            client = AsyncHTTPClient()
            kwargs['callback'] = None

            future = client.fetch(self._url, **kwargs)
            ioloop.IOLoop.current().add_future(future, partial(self.handler, success_cb, failure_cb))
        else:
            client = HTTPClient()
            try:
                client.fetch(self._url, **kwargs)
                success_cb()
            except Exception as e:
                failure_cb(e)

    @staticmethod
    def handler(success, error, future):
        try:
            future.result()
            success()
        except Exception as e:
            error(e)
