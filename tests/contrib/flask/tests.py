import logging

from exam import before, fixture
from mock import patch

from flask import Flask, current_app
from flask.ext.login import LoginManager, AnonymousUserMixin, login_user

from raven.base import Client
from raven.contrib.flask import Sentry
from raven.utils.testutils import TestCase


class TempStoreClient(Client):
    def __init__(self, servers=None, **kwargs):
        self.events = []
        super(TempStoreClient, self).__init__(servers=servers, **kwargs)

    def is_enabled(self):
        return True

    def send(self, **kwargs):
        self.events.append(kwargs)


class User(AnonymousUserMixin):
    is_active = lambda x: True
    is_authenticated = lambda x: True
    get_id = lambda x: 1


def create_app(ignore_exceptions=None):
    import os

    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.urandom(40)

    if ignore_exceptions:
        app.config['RAVEN_IGNORE_EXCEPTIONS'] = ignore_exceptions

    @app.route('/an-error/', methods=['GET', 'POST'])
    def an_error():
        raise ValueError('hello world')

    @app.route('/capture/', methods=['GET', 'POST'])
    def capture_exception():
        try:
            raise ValueError('Boom')
        except:
            current_app.extensions['sentry'].captureException()
        return 'Hello'

    @app.route('/message/', methods=['GET', 'POST'])
    def capture_message():
        current_app.extensions['sentry'].captureMessage('Interesting')
        return 'World'

    @app.route('/an-error-logged-in/', methods=['GET', 'POST'])
    def login():
        login_user(User())
        raise ValueError('hello world')
    return app


def init_login(app):
    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(userid):
        return User()

    return login_manager


class BaseTest(TestCase):
    @fixture
    def app(self):
        return create_app()

    @fixture
    def client(self):
        return self.app.test_client()

    @before
    def bind_sentry(self):
        self.raven = TempStoreClient()
        self.middleware = Sentry(self.app, client=self.raven)

    def make_client_and_raven(self, *args, **kwargs):
        app = create_app(*args, **kwargs)
        raven = TempStoreClient()
        Sentry(app, client=raven)
        return app.test_client(), raven


class FlaskTest(BaseTest):
    def test_does_add_to_extensions(self):
        self.assertIn('sentry', self.app.extensions)
        self.assertEquals(self.app.extensions['sentry'], self.middleware)

    def test_error_handler(self):
        response = self.client.get('/an-error/')
        self.assertEquals(response.status_code, 500)
        self.assertEquals(len(self.raven.events), 1)

        event = self.raven.events.pop(0)

        self.assertTrue('sentry.interfaces.Exception' in event)
        exc = event['sentry.interfaces.Exception']
        self.assertEquals(exc['type'], 'ValueError')
        self.assertEquals(exc['value'], 'hello world')
        self.assertEquals(event['level'], logging.ERROR)
        self.assertEquals(event['message'], 'ValueError: hello world')
        self.assertEquals(event['culprit'], 'tests.contrib.flask.tests in an_error')

    def test_get(self):
        response = self.client.get('/an-error/?foo=bar')
        self.assertEquals(response.status_code, 500)
        self.assertEquals(len(self.raven.events), 1)

        event = self.raven.events.pop(0)

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
        response = self.client.post('/an-error/?biz=baz', data={'foo': 'bar'})
        self.assertEquals(response.status_code, 500)
        self.assertEquals(len(self.raven.events), 1)

        event = self.raven.events.pop(0)

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
        response = self.client.get('/capture/?foo=bar')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(self.raven.events), 1)

        event = self.raven.events.pop(0)

        assert event['message'] == 'ValueError: Boom'
        assert 'sentry.interfaces.Http' in event
        assert 'sentry.interfaces.Exception' in event

    def test_captureMessage_captures_http(self):
        response = self.client.get('/message/?foo=bar')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(self.raven.events), 1)

        event = self.raven.events.pop(0)

        self.assertTrue('sentry.interfaces.Message' in event)
        self.assertTrue('sentry.interfaces.Http' in event)

    @patch('flask.wrappers.RequestBase._load_form_data')
    def test_get_data_handles_disconnected_client(self, lfd):
        from werkzeug.exceptions import ClientDisconnected
        lfd.side_effect = ClientDisconnected
        self.client.post('/capture/?foo=bar', data={'baz': 'foo'})

        event = self.raven.events.pop(0)

        self.assertTrue('sentry.interfaces.Http' in event)
        http = event['sentry.interfaces.Http']
        self.assertEqual({}, http.get('data'))

    def test_error_handler_with_ignored_exception(self):
        client, raven = self.make_client_and_raven(ignore_exceptions=[NameError, ValueError])

        response = client.get('/an-error/')
        self.assertEquals(response.status_code, 500)
        self.assertEquals(len(raven.events), 0)

    def test_error_handler_with_exception_not_ignored(self):
        client, raven = self.make_client_and_raven(ignore_exceptions=[NameError, KeyError])

        response = client.get('/an-error/')
        self.assertEquals(response.status_code, 500)
        self.assertEquals(len(raven.events), 1)

    def test_error_handler_with_empty_ignore_exceptions_list(self):
        client, raven = self.make_client_and_raven(ignore_exceptions=[])

        response = client.get('/an-error/')
        self.assertEquals(response.status_code, 500)
        self.assertEquals(len(raven.events), 1)


class FlaskLoginTest(BaseTest):
    @before
    def setup_login(self):
        self.login_manager = init_login(self.app)

    def test_user(self):
        self.client.get('/an-error-logged-in/')
        event = self.raven.events.pop(0)
        assert event['message'] == 'ValueError: hello world'
        assert 'sentry.interfaces.Http' in event
        assert 'sentry.interfaces.User' in event
