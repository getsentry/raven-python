from exam import fixture

from webtest import TestApp

import bottle

from raven.base import Client
from raven.contrib.bottle import Sentry
from raven.utils.testutils import TestCase


class TempStoreClient(Client):
    def __init__(self, **kwargs):
        self.events = []
        super(TempStoreClient, self).__init__(**kwargs)

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
        except:
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
        assert 'exception' in event

        exc = event['exception']['values'][0]
        self.assertEquals(exc['type'], 'ValueError')

    def test_captureException_captures_http(self):
        response = self.client.get('/capture/?foo=bar')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(self.raven.events), 1)

        event = self.raven.events.pop(0)

        assert event['message'] == 'ValueError: Boom'
        assert 'request' in event
        assert 'exception' in event

    def test_captureMessage_captures_http(self):
        response = self.client.get('/message/?foo=bar')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(self.raven.events), 1)

        event = self.raven.events.pop(0)

        assert 'sentry.interfaces.Message' in event
        assert 'request' in event
