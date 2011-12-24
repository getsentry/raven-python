import logging
from flask import Flask
from raven.base import Client
from raven.contrib.flask import Sentry
from unittest2 import TestCase

class TempStoreClient(Client):
    def __init__(self, servers=None, **kwargs):
        self.events = []
        super(TempStoreClient, self).__init__(servers=servers, **kwargs)

    def send(self, **kwargs):
        self.events.append(kwargs)

def create_app():
    app = Flask(__name__)

    @app.route('/an-error/', methods=['GET', 'POST'])
    def an_error():
        raise ValueError('hello world')

    return app

class FlaskTest(TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_error_handler(self):
        client = TempStoreClient()
        sentry = Sentry(self.app, client=client)
        response = self.client.get('/an-error/?foo=bar')
        self.assertEquals(response.status_code, 500)
        self.assertEquals(len(client.events), 1)

        event = client.events.pop(0)

        self.assertTrue('sentry.interfaces.Exception' in event)
        exc = event['sentry.interfaces.Exception']
        self.assertEquals(exc['type'], 'ValueError')
        self.assertEquals(exc['value'], 'hello world')
        self.assertEquals(event['level'], logging.ERROR)
        self.assertEquals(event['message'], 'ValueError: hello world')
        self.assertEquals(event['culprit'], 'tests.contrib.flask.tests.an_error')

        self.assertTrue('sentry.interfaces.Http' in event)
        http = event['sentry.interfaces.Http']
        self.assertEquals(http['url'], 'http://localhost/an-error/')
        self.assertEquals(http['query_string'], 'foo=bar')
        self.assertEquals(http['method'], 'GET')
        self.assertEquals(http['data'], {'foo': 'bar'})
        self.assertTrue('env' in http)
        env = http['env']
        self.assertTrue('Content-Length' in env)
        self.assertEquals(env['Content-Length'], '0')
        self.assertTrue('Content-Type' in env)
        self.assertEquals(env['Content-Type'], '')
        self.assertTrue('Host' in env)
        self.assertEquals(env['Host'], 'localhost')
