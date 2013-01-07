import logging
from flask import Flask, current_app
from raven.base import Client
from raven.contrib.flask import Sentry
from unittest2 import TestCase
from mock import patch


class TempStoreClient(Client):
    def __init__(self, servers=None, **kwargs):
        self.events = []
        super(TempStoreClient, self).__init__(servers=servers, **kwargs)

    def is_enabled(self):
        return True

    def send(self, **kwargs):
        self.events.append(kwargs)


def create_app():
    app = Flask(__name__)

    @app.route('/an-error/', methods=['GET', 'POST'])
    def an_error():
        raise ValueError('hello world')

    @app.route('/capture/', methods=['GET', 'POST'])
    def capture_exception():
        try:
            raise ValueError('Boom')
        except:
            current_app.sentry.captureException()
        return 'Hello'

    @app.route('/message/', methods=['GET', 'POST'])
    def capture_message():
        current_app.sentry.captureMessage('Interesting')
        return 'World'
    return app


class FlaskTest(TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_does_add_to_extensions(self):
        client = TempStoreClient()
        sentry = Sentry(self.app, client=client)
        self.assertIn('sentry', self.app.extensions)
        self.assertEquals(self.app.extensions['sentry'], sentry)

    def test_error_handler(self):
        client = TempStoreClient()
        sentry = Sentry(self.app, client=client)
        response = self.client.get('/an-error/')
        self.assertEquals(response.status_code, 500)
        self.assertEquals(len(client.events), 1)

        event = client.events.pop(0)

        self.assertTrue('sentry.interfaces.Exception' in event)
        exc = event['sentry.interfaces.Exception']
        self.assertEquals(exc['type'], 'ValueError')
        self.assertEquals(exc['value'], 'hello world')
        self.assertEquals(event['level'], logging.ERROR)
        self.assertEquals(event['message'], 'ValueError: hello world')
        self.assertEquals(event['culprit'], 'tests.contrib.flask.tests in an_error')

    def test_get(self):
        client = TempStoreClient()
        sentry = Sentry(self.app, client=client)
        response = self.client.get('/an-error/?foo=bar')
        self.assertEquals(response.status_code, 500)
        self.assertEquals(len(client.events), 1)

        event = client.events.pop(0)

        self.assertTrue('sentry.interfaces.Http' in event)
        http = event['sentry.interfaces.Http']
        self.assertEquals(http['url'], 'http://localhost/an-error/')
        self.assertEquals(http['query_string'], 'foo=bar')
        self.assertEquals(http['method'], 'GET')
        self.assertEquals(http['data'], {})
        self.assertTrue('headers' in http)
        headers = http['headers']
        self.assertTrue('Content-Length' in headers, headers.keys())
        self.assertEquals(headers['Content-Length'], '0')
        self.assertTrue('Content-Type' in headers, headers.keys())
        self.assertEquals(headers['Content-Type'], '')
        self.assertTrue('Host' in headers, headers.keys())
        self.assertEquals(headers['Host'], 'localhost')
        env = http['env']
        self.assertTrue('SERVER_NAME' in env, env.keys())
        self.assertEquals(env['SERVER_NAME'], 'localhost')
        self.assertTrue('SERVER_PORT' in env, env.keys())
        self.assertEquals(env['SERVER_PORT'], '80')

    def test_post(self):
        client = TempStoreClient()
        sentry = Sentry(self.app, client=client)
        response = self.client.post('/an-error/?biz=baz', data={'foo': 'bar'})
        self.assertEquals(response.status_code, 500)
        self.assertEquals(len(client.events), 1)

        event = client.events.pop(0)

        self.assertTrue('sentry.interfaces.Http' in event)
        http = event['sentry.interfaces.Http']
        self.assertEquals(http['url'], 'http://localhost/an-error/')
        self.assertEquals(http['query_string'], 'biz=baz')
        self.assertEquals(http['method'], 'POST')
        self.assertEquals(http['data'], {'foo': 'bar'})
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
        self.assertTrue('SERVER_PORT' in env, env.keys())
        self.assertEquals(env['SERVER_PORT'], '80')

    def test_captureException_captures_http(self):
        client = TempStoreClient()
        sentry = self.app.sentry = Sentry(self.app, client=client)
        response = self.client.get('/capture/?foo=bar')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(client.events), 1)

        event = client.events.pop(0)

        self.assertTrue('sentry.interfaces.Exception' in event)
        self.assertTrue('sentry.interfaces.Http' in event)

    def test_captureMessage_captures_http(self):
        client = TempStoreClient()
        sentry = self.app.sentry = Sentry(self.app, client=client)
        response = self.client.get('/message/?foo=bar')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(client.events), 1)

        event = client.events.pop(0)

        self.assertTrue('sentry.interfaces.Message' in event)
        self.assertTrue('sentry.interfaces.Http' in event)

    @patch('flask.wrappers.RequestBase._load_form_data')
    def test_get_data_handles_disconnected_client(self, lfd):
        from werkzeug.exceptions import ClientDisconnected
        lfd.side_effect = ClientDisconnected
        client = TempStoreClient()
        sentry = self.app.sentry = Sentry(self.app, client=client)
        response = self.client.post('/capture/?foo=bar', data={'baz': 'foo'})

        event = client.events.pop(0)

        self.assertTrue('sentry.interfaces.Http' in event)
        http = event['sentry.interfaces.Http']
        self.assertEqual({}, http.get('data'))
