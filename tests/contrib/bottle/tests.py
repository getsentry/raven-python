from exam import fixture

from webtest import TestApp

import bottle

from raven.base import Client
from raven.contrib.bottle import Sentry
from raven.utils.testutils import TestCase


class TempStoreClient(Client):
    def __init__(self, servers=None, **kwargs):
        self.events = []
        super(TempStoreClient, self).__init__(servers=servers, **kwargs)

    def is_enabled(self):
        return True

    def send(self, **kwargs):
        self.events.append(kwargs)


def create_app(raven):
    app = bottle.app()
    app.catchall = False
    app = Sentry(app, client=raven)
    tapp = TestApp(app)

    @bottle.route('/error/', ['GET', 'POST'])
    def an_error():
        raise ValueError('hello world')

    @bottle.route('/capture/', ['GET', 'POST'])
    def capture_exception():
        try:
            raise ValueError('Boom')
        except Exception:
            tapp.app.captureException()
        return 'Hello'

    @bottle.route('/message/', ['GET', 'POST'])
    def capture_message():
        tapp.app.captureMessage('Interesting')
        return 'World'

    return tapp


class BaseTest(TestCase):
    @fixture
    def app(self):
        self.raven = TempStoreClient()
        return create_app(self.raven)

    @fixture
    def client(self):
        return self.app


class BottleTest(BaseTest):
    def test_error(self):
        self.assertRaises(ValueError, self.client.get, '/error/?foo=bar')

        self.assertEquals(len(self.raven.events), 1)
        event = self.raven.events.pop(0)
        timeline = event['events']
        self.assertEqual(len(timeline), 2)

        http = timeline[0]
        self.assertEqual(http['type'], 'http_request')
        exc = timeline[1]
        self.assertEqual(exc['type'], 'exception')
        self.assertEquals(exc['exc_type'], 'ValueError')
        self.assertEquals(exc['value'], 'hello world')
        self.assertEquals(event['message'], 'ValueError: hello world')
        self.assertEquals(event['culprit'], 'tests.contrib.bottle.tests in an_error')

    def test_captureException_captures_http(self):
        response = self.client.get('/capture/?foo=bar')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(self.raven.events), 1)

        event = self.raven.events.pop(0)
        timeline = event['events']
        self.assertEqual(len(timeline), 2)

        http = timeline[0]
        self.assertEqual(http['type'], 'http_request')
        exc = timeline[1]
        self.assertEqual(exc['type'], 'exception')

        self.assertEqual(event['message'], 'ValueError: Boom')

    def test_captureMessage_captures_http(self):
        response = self.client.get('/message/?foo=bar')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(self.raven.events), 1)

        event = self.raven.events.pop(0)
        timeline = event['events']
        self.assertEqual(len(timeline), 2)

        http = timeline[0]
        self.assertEqual(http['type'], 'http_request')
        exc = timeline[1]
        self.assertEqual(exc['type'], 'message')
