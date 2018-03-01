import json
import logging
import pytest
import sys

from exam import before, fixture
from mock import patch, Mock

from raven.contrib.sanic import Sentry, logging_configured
from raven.handlers.logging import SentryHandler
from raven.utils.testutils import InMemoryClient, TestCase


if sys.version_info >= (3, 5):
    from sanic import Sanic, response

# When using test_client, Sanic will run the server at 127.0.0.1:42101.
# For ease of reading, let's establish that as a constant.
BASE_URL = '127.0.0.1:42101'

def create_app(ignore_exceptions=None, debug=False, **config):
    import os
    app = Sanic(__name__)
    for key, value in config.items():
        app.config[key] = value

    app.debug = debug

    if ignore_exceptions:
        app.config['RAVEN_IGNORE_EXCEPTIONS'] = ignore_exceptions

    @app.route('/an-error/', methods=['GET', 'POST'])
    def an_error(request):
        raise ValueError('hello world')

    @app.route('/log-an-error/', methods=['GET'])
    def log_an_error(request):
        logger = logging.getLogger('random-logger')
        logger.error('Log an error')
        return response.text('Hello')

    @app.route('/capture/', methods=['GET', 'POST'])
    def capture_exception(request):
        try:
            raise ValueError('Boom')
        except Exception:
            request.app.extensions['sentry'].captureException()
        return response.text('Hello')

    @app.route('/message/', methods=['GET', 'POST'])
    def capture_message(request):
        request.app.extensions['sentry'].captureMessage('Interesting')
        return response.text('World')

    return app

@pytest.mark.skipif(sys.version_info < (3,5), reason="Requires Python 3.5+.")
class BaseTest(TestCase):
    @fixture
    def app(self):
        return create_app()

    @fixture
    def client(self):
        return self.app.test_client

    @before
    def bind_sentry(self):
        self.raven = InMemoryClient()
        self.middleware = Sentry(self.app, client=self.raven)

    def make_client_and_raven(self, logging=False, *args, **kwargs):
        app = create_app(*args, **kwargs)
        raven = InMemoryClient()
        Sentry(app, logging=logging, client=raven)
        return app.test_client, raven, app

@pytest.mark.skipif(sys.version_info < (3,5), reason="Requires Python 3.5+.")
class SanicTest(BaseTest):
    def test_does_add_to_extensions(self):
        self.assertIn('sentry', self.app.extensions)
        self.assertEquals(self.app.extensions['sentry'], self.middleware)

    def test_error_handler(self):
        request, response = self.client.get('/an-error/')
        self.assertEquals(response.status, 500)
        self.assertEquals(len(self.raven.events), 1)

        event = self.raven.events.pop(0)

        assert 'exception' in event
        exc = event['exception']['values'][-1]
        self.assertEquals(exc['type'], 'ValueError')
        self.assertEquals(exc['value'], 'hello world')
        self.assertEquals(event['level'], logging.ERROR)
        self.assertEquals(event['message'], 'ValueError: hello world')

    def test_capture_plus_logging(self):
        client, raven, app = self.make_client_and_raven(
            debug=False, logging=True)
        client.get('/an-error/')
        client.get('/log-an-error/')
        assert len(raven.events) == 2

    def test_get(self):
        request, response = self.client.get('/an-error/?foo=bar')
        self.assertEquals(response.status, 500)
        self.assertEquals(len(self.raven.events), 1)

        event = self.raven.events.pop(0)

        assert 'request' in event
        http = event['request']
        self.assertEquals(http['url'], 'http://{0}/an-error/'.format(BASE_URL))
        self.assertEquals(http['query_string'], 'foo=bar')
        self.assertEquals(http['method'], 'GET')
        self.assertEquals(http['data'], {})
        self.assertTrue('headers' in http)
        headers = http['headers']
        self.assertTrue('host' in headers, headers.keys())
        self.assertEqual(headers['host'], BASE_URL)
        self.assertTrue('user-agent' in headers, headers.keys())
        self.assertTrue('aiohttp' in headers['user-agent'])

    def test_post_form(self):
        request, response = self.client.post('/an-error/?biz=baz', data={'foo': 'bar'})
        self.assertEquals(response.status, 500)
        self.assertEquals(len(self.raven.events), 1)
        event = self.raven.events.pop(0)

        assert 'request' in event
        http = event['request']
        self.assertEquals(http['url'], 'http://{0}/an-error/'.format(BASE_URL))
        self.assertEquals(http['query_string'], 'biz=baz')
        self.assertEquals(http['method'], 'POST')
        self.assertEquals(http['data'], {'foo': ['bar']})
        self.assertTrue('headers' in http)
        headers = http['headers']
        self.assertTrue('host' in headers, headers.keys())
        self.assertEqual(headers['host'], BASE_URL)
        self.assertTrue('user-agent' in headers, headers.keys())
        self.assertTrue('aiohttp' in headers['user-agent'])

    def test_post_json(self):
        request, response = self.client.post(
            '/an-error/?biz=baz', data=json.dumps({'foo': 'bar'}),
            headers={'content-type': 'application/json'})
        self.assertEquals(response.status, 500)
        self.assertEquals(len(self.raven.events), 1)
        event = self.raven.events.pop(0)
        assert 'request' in event
        http = event['request']
        self.assertEquals(http['url'], 'http://{0}/an-error/'.format(BASE_URL))
        self.assertEquals(http['query_string'], 'biz=baz')
        self.assertEquals(http['method'], 'POST')
        self.assertEquals(http['data'], {'foo': 'bar'})
        self.assertTrue('headers' in http)
        headers = http['headers']
        self.assertTrue('host' in headers, headers.keys())
        self.assertEqual(headers['host'], BASE_URL)
        self.assertTrue('user-agent' in headers, headers.keys())
        self.assertTrue('aiohttp' in headers['user-agent'])

    def test_captureException_captures_http(self):
        request, response = self.client.get('/capture/?foo=bar')
        self.assertEquals(response.status, 200)
        self.assertEquals(len(self.raven.events), 1)

        event = self.raven.events.pop(0)
        self.assertEquals(event['event_id'], response.headers['X-Sentry-ID'])

        assert event['message'] == 'ValueError: Boom'
        print(event)
        assert 'request' in event
        assert 'exception' in event

    def test_captureMessage_captures_http(self):
        request, response = self.client.get('/message/?foo=bar')
        self.assertEquals(response.status, 200)
        self.assertEquals(len(self.raven.events), 1)

        event = self.raven.events.pop(0)
        self.assertEquals(event['event_id'], response.headers['X-Sentry-ID'])

        assert 'sentry.interfaces.Message' in event
        assert 'request' in event

    def test_captureException_sets_last_event_id(self):
        try:
            raise ValueError
        except Exception:
            self.middleware.captureException()
        else:
            self.fail()

        event_id = self.raven.events.pop(0)['event_id']
        assert self.middleware.last_event_id == event_id

    def test_captureMessage_sets_last_event_id(self):
        self.middleware.captureMessage('foo')

        event_id = self.raven.events.pop(0)['event_id']
        assert self.middleware.last_event_id == event_id

    def test_logging_setup_signal(self):
        app = Sanic(__name__)

        mock_handler = Mock()

        def receiver(sender, *args, **kwargs):
            self.assertIn("exclude", kwargs)
            mock_handler(*args, **kwargs)

        logging_configured.connect(receiver)
        raven = InMemoryClient()

        Sentry(
            app, client=raven, logging=True,
            logging_exclusions=("excluded_logger",))

        mock_handler.assert_called()

    def test_check_client_type(self):
        self.assertRaises(TypeError, lambda _: Sentry(self.app, "oops, I'm putting my DSN instead"))

    def test_uses_dsn(self):
        app = Sanic(__name__)
        sentry = Sentry(app, dsn='http://public:secret@example.com/1')
        assert sentry.client.remote.base_url == 'http://example.com'

    def test_binds_default_include_paths(self):
        app = Sanic(__name__)
        sentry = Sentry(app, dsn='http://public:secret@example.com/1')
        assert sentry.client.include_paths == set([app.name])

    def test_overrides_default_include_paths(self):
        app = Sanic(__name__)
        app.config['SENTRY_CONFIG'] = {'include_paths': ['foo.bar']}
        sentry = Sentry(app, dsn='http://public:secret@example.com/1')
        assert sentry.client.include_paths == set(['foo.bar'])
