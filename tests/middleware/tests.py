from __future__ import with_statement

import logging
import webob
from exam import fixture
from raven.utils.testutils import TestCase

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


class TestMiddlewareTestCase(TestCase):
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
        assert iterable.closed

        assert len(self.client.events) == 1
        event = self.client.events.pop(0)

        assert 'sentry.interfaces.Exception' in event
        exc = event['sentry.interfaces.Exception']
        assert exc['type'] == 'ValueError'
        assert exc['value'] == 'hello world'
        assert event['level'] == logging.ERROR
        assert event['message'] == 'ValueError: hello world'

        assert 'sentry.interfaces.Http' in event
        http = event['sentry.interfaces.Http']
        assert http['url'] == 'http://localhost/an-error'
        assert http['query_string'] == 'foo=bar'
        assert http['method'] == 'GET'
        # self.assertEquals(http['data'], {'foo': 'bar'})
        headers = http['headers']
        assert 'Host' in headers, headers.keys()
        assert headers['Host'] == 'localhost:80'
        env = http['env']
        assert 'SERVER_NAME' in env, env.keys()
        assert env['SERVER_NAME'] == 'localhost'
        assert 'SERVER_PORT' in env, env.keys()
        assert env['SERVER_PORT'] == '80'
