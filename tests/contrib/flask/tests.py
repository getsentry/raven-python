import logging

from exam import before, fixture
from mock import patch

from flask import Flask, current_app, g
from flask.ext.login import LoginManager, AnonymousUserMixin, login_user

from raven.base import Client
from raven.contrib.flask import Sentry
from raven.utils.testutils import TestCase
from raven.handlers.logging import SentryHandler


class TempStoreClient(Client):
    def __init__(self, **kwargs):
        self.events = []
        super(TempStoreClient, self).__init__(**kwargs)

    def is_enabled(self):
        return True

    def send(self, **kwargs):
        self.events.append(kwargs)


class User(AnonymousUserMixin):
    is_active = lambda x: True
    is_authenticated = lambda x: True
    get_id = lambda x: 1
    name = 'TestUser'

    def to_dict(self):
        return {
            'id': self.get_id(),
            'name': self.name
        }


def create_app(ignore_exceptions=None, debug=False, **config):
    import os

    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.urandom(40)
    for key, value in config.items():
        app.config[key] = value

    app.debug = debug

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

    @app.route('/login/', methods=['GET', 'POST'])
    def login():
        login_user(User())
        return "hello world"
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
        return app.test_client(), raven, app


class FlaskTest(BaseTest):
    def test_does_add_to_extensions(self):
        self.assertIn('sentry', self.app.extensions)
        self.assertEquals(self.app.extensions['sentry'], self.middleware)

    def test_error_handler(self):
        response = self.client.get('/an-error/')
        self.assertEquals(response.status_code, 500)
        self.assertEquals(len(self.raven.events), 1)

        event = self.raven.events.pop(0)

        assert 'exception' in event
        exc = event['exception']['values'][0]
        self.assertEquals(exc['type'], 'ValueError')
        self.assertEquals(exc['value'], 'hello world')
        self.assertEquals(event['level'], logging.ERROR)
        self.assertEquals(event['message'], 'ValueError: hello world')
        self.assertEquals(event['culprit'], 'tests.contrib.flask.tests in an_error')

    def test_capture_plus_logging(self):
        client, raven, app = self.make_client_and_raven(debug=False)
        app.logger.addHandler(SentryHandler(raven))
        client.get('/an-error/')
        assert len(raven.events) == 1

    def test_get(self):
        response = self.client.get('/an-error/?foo=bar')
        self.assertEquals(response.status_code, 500)
        self.assertEquals(len(self.raven.events), 1)

        event = self.raven.events.pop(0)

        assert 'request' in event
        http = event['request']
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

        assert 'request' in event
        http = event['request']
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
        self.assertEquals(event['event_id'], response.headers['X-Sentry-ID'])

        assert event['message'] == 'ValueError: Boom'
        assert 'request' in event
        assert 'exception' in event

    def test_captureMessage_captures_http(self):
        response = self.client.get('/message/?foo=bar')
        self.assertEquals(response.status_code, 200)
        self.assertEquals(len(self.raven.events), 1)

        event = self.raven.events.pop(0)
        self.assertEquals(event['event_id'], response.headers['X-Sentry-ID'])

        assert 'sentry.interfaces.Message' in event
        assert 'request' in event

    @patch('flask.wrappers.RequestBase._load_form_data')
    def test_get_data_handles_disconnected_client(self, lfd):
        from werkzeug.exceptions import ClientDisconnected
        lfd.side_effect = ClientDisconnected
        self.client.post('/capture/?foo=bar', data={'baz': 'foo'})

        event = self.raven.events.pop(0)

        assert 'request' in event
        http = event['request']
        self.assertEqual({}, http.get('data'))

    def test_wrap_wsgi_status(self):
        _, _, app_debug = self.make_client_and_raven(debug=True)
        self.assertFalse(app_debug.extensions['sentry'].wrap_wsgi)

        _, _, app_ndebug = self.make_client_and_raven(debug=False)
        self.assertTrue(app_ndebug.extensions['sentry'].wrap_wsgi)

    def test_error_handler_with_ignored_exception(self):
        client, raven, _ = self.make_client_and_raven(ignore_exceptions=[NameError, ValueError])

        response = client.get('/an-error/')
        self.assertEquals(response.status_code, 500)
        self.assertEquals(len(raven.events), 0)

    def test_error_handler_with_exception_not_ignored(self):
        client, raven, _ = self.make_client_and_raven(ignore_exceptions=[NameError, KeyError])

        response = client.get('/an-error/')
        self.assertEquals(response.status_code, 500)
        self.assertEquals(len(raven.events), 1)

    def test_error_handler_with_empty_ignore_exceptions_list(self):
        client, raven, _ = self.make_client_and_raven(ignore_exceptions=[])

        response = client.get('/an-error/')
        self.assertEquals(response.status_code, 500)
        self.assertEquals(len(raven.events), 1)

    def test_captureException_sets_last_event_id(self):
        with self.app.test_request_context('/'):
            try:
                raise ValueError
            except Exception:
                self.middleware.captureException()
            else:
                self.fail()

            event_id = self.raven.events.pop(0)['event_id']
            assert self.middleware.last_event_id == event_id
            assert g.sentry_event_id == event_id

    def test_captureMessage_sets_last_event_id(self):
        with self.app.test_request_context('/'):
            self.middleware.captureMessage('foo')

            event_id = self.raven.events.pop(0)['event_id']
            assert self.middleware.last_event_id == event_id
            assert g.sentry_event_id == event_id

    def test_logging_setup_with_exclusion_list(self):
        app = Flask(__name__)
        raven = TempStoreClient()

        Sentry(app, client=raven, logging=True,
            logging_exclusions=("excluded_logger",))

        excluded_logger = logging.getLogger("excluded_logger")
        self.assertFalse(excluded_logger.propagate)

        some_other_logger = logging.getLogger("some_other_logger")
        self.assertTrue(some_other_logger.propagate)


class FlaskLoginTest(BaseTest):

    @fixture
    def app(self):
        return create_app(SENTRY_USER_ATTRS=['name'])

    @before
    def setup_login(self):
        self.login_manager = init_login(self.app)

    def test_user(self):
        self.client.get('/login/')
        self.client.get('/an-error/')
        event = self.raven.events.pop(0)
        assert event['message'] == 'ValueError: hello world'
        assert 'request' in event
        assert 'user' in event
        self.assertDictEqual(event['user'], User().to_dict())
