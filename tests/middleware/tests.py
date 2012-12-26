from __future__ import with_statement

import logging
import webob
from exam import fixture
from unittest2 import TestCase

from raven.base import Client
from raven.middleware import Sentry


class TempStoreClient(Client):
    def __init__(self, servers=None, **kwargs):
        self.events = []
        super(TempStoreClient, self).__init__(servers=servers, **kwargs)

    def is_enabled(self):
        return True

    def send(self, **kwargs):
        self.events.append(kwargs)


class ErroringIterable(object):
    def __init__(self):
        self.closed = False

    def __iter__(self):
        raise ValueError('hello world')

    def close(self):
        self.closed = True


class ExampleApp(object):
    def __init__(self, iterable):
        self.iterable = iterable

    def __call__(self, environ, start_response):
        return self.iterable


class MiddlewareTestCase(TestCase):
    @fixture
    def client(self):
        return TempStoreClient()

    @fixture
    def request(self):
        return webob.Request.blank('/an-error?foo=bar')

    def test_captures_error_in_iteration(self):
        iterable = ErroringIterable()
        app = ExampleApp(iterable)
        middleware = Sentry(app, client=self.client)

        response = middleware(self.request.environ, lambda *args: None)

        with self.assertRaises(ValueError):
            response = list(response)

        # TODO: this should be a separate test
        self.assertTrue(iterable.closed, True)

        self.assertEquals(len(self.client.events), 1)
        event = self.client.events.pop(0)

        self.assertTrue('sentry.interfaces.Exception' in event)
        exc = event['sentry.interfaces.Exception']
        self.assertEquals(exc['type'], 'ValueError')
        self.assertEquals(exc['value'], 'hello world')
        self.assertEquals(event['level'], logging.ERROR)
        self.assertEquals(event['message'], 'ValueError: hello world')

        self.assertTrue('sentry.interfaces.Http' in event)
        http = event['sentry.interfaces.Http']
        self.assertEquals(http['url'], 'http://localhost/an-error')
        self.assertEquals(http['query_string'], 'foo=bar')
        self.assertEquals(http['method'], 'GET')
        # self.assertEquals(http['data'], {'foo': 'bar'})
        headers = http['headers']
        self.assertTrue('Host' in headers, headers.keys())
        self.assertEquals(headers['Host'], 'localhost:80')
        env = http['env']
        self.assertTrue('SERVER_NAME' in env, env.keys())
        self.assertEquals(env['SERVER_NAME'], 'localhost')
        self.assertTrue('SERVER_PORT' in env, env.keys())
        self.assertEquals(env['SERVER_PORT'], '80')
