from exam import fixture
from paste.fixture import TestApp

from raven.base import Client
from raven.contrib.webpy import SentryApplication
from raven.utils.testutils import TestCase


class TempStoreClient(Client):
    def __init__(self, **kwargs):
        self.events = []
        super(TempStoreClient, self).__init__(**kwargs)

    def is_enabled(self):
        return True

    def send(self, **kwargs):
        self.events.append(kwargs)


class TestEndpoint(object):
    def GET(self):
        raise ValueError('That\'s what she said')

    def POST(self):
        raise TypeError('Potato')


urls = (
    '/test', TestEndpoint
)


def create_app(client):
    return SentryApplication(client=client, mapping=urls)


class WebPyTest(TestCase):
    @fixture
    def app(self):
        self.store = TempStoreClient()
        return create_app(self.store)

    @fixture
    def client(self):
        return TestApp(self.app.wsgifunc())

    def test_get(self):
        resp = self.client.get('/test', expect_errors=True)

        self.assertEquals(resp.status, 500)
        self.assertEquals(len(self.store.events), 1)

        event = self.store.events.pop()
        assert 'exception' in event
        exc = event['exception']['values'][0]
        self.assertEquals(exc['type'], 'ValueError')
        self.assertEquals(exc['value'], 'That\'s what she said')
        self.assertEquals(event['message'], 'ValueError: That\'s what she said')
        self.assertEquals(event['culprit'], 'tests.contrib.webpy.tests in GET')

    def test_post(self):
        response = self.client.post('/test?biz=baz', params={'foo': 'bar'}, expect_errors=True)
        self.assertEquals(response.status, 500)
        self.assertEquals(len(self.store.events), 1)

        event = self.store.events.pop()

        assert 'request' in event
        http = event['request']
        self.assertEquals(http['url'], 'http://localhost/test')
        self.assertEquals(http['query_string'], '?biz=baz')
        self.assertEquals(http['method'], 'POST')
        self.assertEquals(http['data'], 'foo=bar')
        self.assertTrue('headers' in http)
        headers = http['headers']
        self.assertTrue('Content-Length' in headers, headers.keys())
        self.assertEquals(headers['Content-Length'], '7')
        self.assertTrue('Content-Type' in headers, headers.keys())
        self.assertEquals(headers['Content-Type'], 'application/x-www-form-urlencoded')
        self.assertTrue('Host' in headers, headers.keys())
        self.assertEquals(headers['Host'], 'localhost')
        env = http['env']
        self.assertTrue('SERVER_NAME' in env, env.keys())
        self.assertEquals(env['SERVER_NAME'], 'localhost')
