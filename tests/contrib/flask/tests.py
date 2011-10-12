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
        self.assertEquals(event['class_name'], 'ValueError')
        self.assertEquals(event['level'], logging.ERROR)
        self.assertEquals(event['message'], 'hello world')
        self.assertEquals(event['url'], 'http://localhost/an-error/?foo=bar')
        self.assertEquals(event['view'], 'tests.contrib.flask.tests.an_error')

