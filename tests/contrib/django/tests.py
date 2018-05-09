# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, with_statement

import datetime
import django
import logging
import mock
import pytest
import re
import sys

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.core.signals import got_request_exception
from django.core.handlers.wsgi import WSGIRequest
from django.http import QueryDict
from django.template import TemplateSyntaxError
from django.test import TestCase
from django.test.client import Client as DjangoTestClient, ClientHandler as DjangoTestClientHandler
from django.utils.translation import gettext_lazy
from exam import fixture

try:
    from django.urls import reverse
except ImportError:
    # For Django version less than 1.10.
    from django.core.urlresolvers import reverse

from raven.base import Client
from raven.utils.compat import StringIO, iteritems, PY2, string_types, text_type
from raven.contrib.django.client import DjangoClient, record_sql
from raven.contrib.django.celery import CeleryClient
from raven.contrib.django.handlers import SentryHandler
from raven.contrib.django.models import (
    SentryDjangoHandler, client, get_client
)
from raven.contrib.django.middleware.wsgi import Sentry
from raven.contrib.django.templatetags.raven import sentry_public_dsn
from raven.contrib.django.views import is_valid_origin
from raven.transport import HTTPTransport
from raven.utils.serializer import transform

from .views import AppError

#from .models import MyTestModel

DJANGO_15 = django.VERSION >= (1, 5, 0)
DJANGO_18 = django.VERSION >= (1, 8, 0)
DJANGO_110 = django.VERSION >= (1, 10, 0)

MIDDLEWARE_ATTR = 'MIDDLEWARE' if DJANGO_110 else 'MIDDLEWARE_CLASSES'


def make_request():
    return WSGIRequest(environ={
        'wsgi.input': StringIO(),
        'REQUEST_METHOD': 'POST',
        'SERVER_NAME': 'testserver',
        'SERVER_PORT': '80',
        'CONTENT_TYPE': 'text/html',
        'ACCEPT': 'text/html',
    })


class MockClientHandler(DjangoTestClientHandler):
    def __call__(self, environ, start_response=[]):
        # this pretends doesn't require start_response
        return super(MockClientHandler, self).__call__(environ)


class MockSentryMiddleware(Sentry):
    def __call__(self, environ, start_response=[]):
        # this pretends doesn't require start_response
        return list(super(MockSentryMiddleware, self).__call__(environ, start_response))


class MockClient(DjangoClient):
    def __init__(self, *args, **kwargs):
        self.events = []
        super(MockClient, self).__init__(*args, **kwargs)

    def send(self, **kwargs):
        self.events.append(kwargs)

    def is_enabled(self, **kwargs):
        return True


class DisabledMockClient(MockClient):
    def is_enabled(self, **kwargs):
        return False


class Settings(object):
    """
    Allows you to define settings that are required for this function to work.

    >>> with Settings(SENTRY_LOGIN_URL='foo'): #doctest: +SKIP
    >>>     print settings.SENTRY_LOGIN_URL #doctest: +SKIP
    """

    NotDefined = object()

    def __init__(self, **overrides):
        self.overrides = overrides
        self._orig = {}

    def __enter__(self):
        for k, v in iteritems(self.overrides):
            self._orig[k] = getattr(settings, k, self.NotDefined)
            setattr(settings, k, v)

    def __exit__(self, exc_type, exc_value, traceback):
        for k, v in iteritems(self._orig):
            if v is self.NotDefined:
                delattr(settings, k)
            else:
                setattr(settings, k, v)


class ClientProxyTest(TestCase):
    def test_proxy_responds_as_client(self):
        assert get_client() == client

    @mock.patch.object(MockClient, 'captureMessage')
    def test_basic(self, captureMessage):
        client.captureMessage(message='foo')
        captureMessage.assert_called_once_with(message='foo')


@pytest.mark.usefixtures("user_instance")
class DjangoClientTest(TestCase):
    # Fixture setup/teardown
    urls = 'tests.contrib.django.urls'

    def setUp(self):
        self.raven = get_client()
        self.handler = SentryDjangoHandler(self.raven)
        self.handler.install()
        self.addCleanup(self.handler.uninstall)

    def test_basic(self):
        self.raven.captureMessage(message='foo')
        assert len(self.raven.events) == 1
        event = self.raven.events.pop(0)
        assert 'sentry.interfaces.Message' in event
        message = event['sentry.interfaces.Message']
        assert message['message'] == 'foo'
        assert event['level'] == logging.ERROR
        assert event['message'] == 'foo'
        assert isinstance(event['timestamp'], datetime.datetime)

    def test_signal_integration(self):
        try:
            int(None)
        except Exception:
            got_request_exception.send(sender=self.__class__, request=None)
        else:
            self.fail('Expected an exception.')

        assert len(self.raven.events) == 1
        event = self.raven.events.pop(0)
        assert 'exception' in event
        exc = event['exception']['values'][-1]
        assert exc['type'] == 'TypeError'
        assert exc['value'], "int() argument must be a string or a number == not 'NoneType'"
        assert event['level'] == logging.ERROR
        assert event['message'], "TypeError: int() argument must be a string or a number == not 'NoneType'"

    @pytest.mark.skipif(sys.version_info[:2] == (2, 6), reason='Python 2.6')
    def test_view_exception(self):
        path = reverse('sentry-raise-exc')
        self.assertRaises(Exception, self.client.get, path)

        assert len(self.raven.events) == 1
        event = self.raven.events.pop(0)
        assert 'exception' in event
        exc = event['exception']['values'][-1]
        assert exc['type'] == 'Exception'
        assert exc['value'] == 'view exception'
        assert event['level'] == logging.ERROR
        assert event['message'] == 'Exception: view exception'
        assert 'request' in event
        assert event['request']['url'] == 'http://testserver{}'.format(path)

    def test_request_data_unavailable_if_request_is_read(self):
        with Settings(**{MIDDLEWARE_ATTR: []}):
            path = reverse('sentry-readrequest-raise-exc')
            self.assertRaises(
                AppError,
                self.client.post,
                path,
                '{"a":"b"}',
                content_type='application/json')
        assert len(self.raven.events) == 1
        event = self.raven.events.pop(0)
        assert event['request']['data'] == '<unavailable>'

    def test_djangorestframeworkcompatmiddleware_fills_request_data(self):
        with Settings(**{MIDDLEWARE_ATTR: [
            'raven.contrib.django.middleware.DjangoRestFrameworkCompatMiddleware']}):
            path = reverse('sentry-readrequest-raise-exc')
            self.assertRaises(
                AppError,
                self.client.post,
                path,
                '{"a":"b"}',
                content_type='application/json')
        assert len(self.raven.events) == 1
        event = self.raven.events.pop(0)
        assert event['request']['data'] == '{"a":"b"}'

    def test_capture_event_with_request_middleware(self):
        path = reverse('sentry-trigger-event')
        resp = self.client.get(path)
        assert resp.status_code == 200

        assert len(self.raven.events) == 1
        event = self.raven.events.pop(0)
        assert event['message'] == 'test'
        assert 'request' in event
        assert event['request']['url'] == 'http://testserver{}'.format(path)

    def test_user_info(self):
        with Settings(**{MIDDLEWARE_ATTR: [
                'django.contrib.sessions.middleware.SessionMiddleware',
                'django.contrib.auth.middleware.AuthenticationMiddleware']}):

            self.assertRaises(Exception, self.client.get, reverse('sentry-raise-exc'))

            assert len(self.raven.events) == 1
            event = self.raven.events.pop(0)
            assert 'user' in event

            user_info = event['user']
            assert user_info == {'ip_address': '127.0.0.1'}

            assert self.client.login(username='admin', password='password')

            self.assertRaises(Exception, self.client.get, reverse('sentry-raise-exc'))

            assert len(self.raven.events) == 1
            event = self.raven.events.pop(0)
            assert 'user' in event
            user_info = event['user']
            assert user_info == {
                'ip_address': '127.0.0.1',
                'username': self.user.username,
                'id': self.user.id,
                'email': self.user.email,
            }

    @pytest.mark.skipif(not DJANGO_15, reason='< Django 1.5')
    def test_get_user_info_abstract_user(self):

        from django.db import models
        from django.http import HttpRequest
        from django.contrib.auth.models import AbstractBaseUser

        class MyUser(AbstractBaseUser):
            USERNAME_FIELD = 'username'

            username = models.CharField(max_length=32)
            email = models.EmailField()

        user = MyUser(
            username='admin',
            email='admin@example.com',
            id=1,
        )

        request = HttpRequest()
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        request.user = user
        user_info = self.raven.get_user_info(request)
        assert user_info == {
            'ip_address': '127.0.0.1',
            'username': user.username,
            'id': user.id,
            'email': user.email,
        }

        request = HttpRequest()
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        request.META['HTTP_X_FORWARDED_FOR'] = '1.1.1.1, 2.2.2.2'
        request.user = user
        user_info = self.raven.get_user_info(request)
        assert user_info == {
            'ip_address': '1.1.1.1',
            'username': user.username,
            'id': user.id,
            'email': user.email,
        }

    @pytest.mark.skipif(not DJANGO_110, reason='< Django 1.10')
    def test_get_user_info_is_authenticated_property(self):
        from django.db import models
        from django.http import HttpRequest
        from django.contrib.auth.models import AbstractBaseUser

        class MyUser(AbstractBaseUser):
            USERNAME_FIELD = 'username'
            username = models.CharField(max_length=32)
            email = models.EmailField()

            @property
            def is_authenticated(self):
                return True

        user = MyUser(
            username='admin',
            email='admin@example.com',
            id=1,
        )

        request = HttpRequest()
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        request.user = user
        user_info = self.raven.get_user_info(request)
        assert user_info == {
            'ip_address': '127.0.0.1',
            'username': user.username,
            'id': user.id,
            'email': user.email,
        }

        request = HttpRequest()
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        request.META['HTTP_X_FORWARDED_FOR'] = '1.1.1.1, 2.2.2.2'
        request.user = user
        user_info = self.raven.get_user_info(request)
        assert user_info == {
            'ip_address': '1.1.1.1',
            'username': user.username,
            'id': user.id,
            'email': user.email,
        }

    def test_request_middleware_exception(self):
        with Settings(**{MIDDLEWARE_ATTR: ['tests.contrib.django.middleware.BrokenRequestMiddleware']}):
            self.assertRaises(ImportError, self.client.get, reverse('sentry-raise-exc'))

            assert len(self.raven.events) == 1
            event = self.raven.events.pop(0)

            assert 'exception' in event
            exc = event['exception']['values'][-1]
            assert exc['type'] == 'ImportError'
            assert exc['value'] == 'request'
            assert event['level'] == logging.ERROR
            assert event['message'] == 'ImportError: request'

    def test_response_middlware_exception(self):
        if django.VERSION[:2] < (1, 3):
            return
        with Settings(**{MIDDLEWARE_ATTR: ['tests.contrib.django.middleware.BrokenResponseMiddleware']}):
            self.assertRaises(ImportError, self.client.get, reverse('sentry-no-error'))

            assert len(self.raven.events) == 1
            event = self.raven.events.pop(0)

            assert 'exception' in event
            exc = event['exception']['values'][-1]
            assert exc['type'] == 'ImportError'
            assert exc['value'] == 'response'
            assert event['level'] == logging.ERROR
            assert event['message'] == 'ImportError: response'

    def test_broken_500_handler_with_middleware(self):
        with Settings(BREAK_THAT_500=True, INSTALLED_APPS=['raven.contrib.django']):
            client = DjangoTestClient(REMOTE_ADDR='127.0.0.1')
            client.handler = MockSentryMiddleware(MockClientHandler())

            self.assertRaises(Exception, client.get, reverse('sentry-raise-exc'))
            assert len(self.raven.events) == 2 or 4  # TODO: ash remove duplicate client events
            event = self.raven.events.pop(0)

            assert 'exception' in event
            exc = event['exception']['values'][-1]
            assert exc['type'] == 'Exception'
            assert exc['value'] == 'view exception'
            assert event['level'] == logging.ERROR
            assert event['message'] == 'Exception: view exception'

            event = self.raven.events.pop(0)

            assert 'exception' in event
            exc = event['exception']['values'][-1]
            assert exc['type'] == 'ValueError'
            assert exc['value'] == 'handler500'
            assert event['level'] == logging.ERROR
            assert event['message'] == 'ValueError: handler500'

    def test_view_middleware_exception(self):
        with Settings(**{MIDDLEWARE_ATTR: ['tests.contrib.django.middleware.BrokenViewMiddleware']}):
            self.assertRaises(ImportError, self.client.get, reverse('sentry-raise-exc'))

            assert len(self.raven.events) == 1
            event = self.raven.events.pop(0)

            assert 'exception' in event
            exc = event['exception']['values'][-1]
            assert exc['type'] == 'ImportError'
            assert exc['value'] == 'view'
            assert event['level'] == logging.ERROR
            assert event['message'] == 'ImportError: view'

    @pytest.mark.skipif(DJANGO_18, reason='Django 1.8+ not supported')
    def test_template_name_as_view(self):
        self.assertRaises(TemplateSyntaxError, self.client.get, reverse('sentry-template-exc'))

        assert len(self.raven.events) == 1
        event = self.raven.events.pop(0)

        assert event['culprit'] == 'error.html'

    # def test_request_in_logging(self):
    #     resp = self.client.get(reverse('sentry-log-request-exc'))
    #     assert resp.status_code == 200

    #     assert len(self.raven.events) == 1
    #     event = self.raven.events.pop(0)

    #     assert event['culprit'] == 'tests.contrib.django.views in logging_request_exc'
    #     assert event['data']['META']['REMOTE_ADDR'] == '127.0.0.1'

    # TODO: Python bug #10805
    @pytest.mark.skipif(not PY2, reason='Python 2')
    def test_record_none_exc_info(self):
        # sys.exc_info can return (None, None, None) if no exception is being
        # handled anywhere on the stack. See:
        #  http://docs.python.org/library/sys.html#sys.exc_info
        record = logging.LogRecord(
            'foo',
            logging.INFO,
            pathname=None,
            lineno=None,
            msg='test',
            args=(),
            exc_info=(None, None, None),
        )
        handler = SentryHandler()
        handler.emit(record)

        assert len(self.raven.events) == 1
        event = self.raven.events.pop(0)
        assert event['message'] == 'test'

    def test_404_middleware(self):
        with Settings(**{MIDDLEWARE_ATTR: ['raven.contrib.django.middleware.Sentry404CatchMiddleware']}):
            resp = self.client.get('/non-existent-page')
            assert resp.status_code == 404

            assert len(self.raven.events) == 1, [e['message'] for e in self.raven.events]
            event = self.raven.events.pop(0)

            assert event['level'] == logging.INFO
            assert event['logger'] == 'http404'

            assert 'request' in event
            http = event['request']
            assert http['url'] == 'http://testserver/non-existent-page'
            assert http['method'] == 'GET'
            assert http['query_string'] == ''
            assert http['data'] is None

    def test_404_middleware_when_disabled(self):
        extra_settings = {
            MIDDLEWARE_ATTR: ['raven.contrib.django.middleware.Sentry404CatchMiddleware'],
            'SENTRY_CLIENT': 'tests.contrib.django.tests.DisabledMockClient',
        }
        with Settings(**extra_settings):
            resp = self.client.get('/non-existent-page')
            assert resp.status_code == 404
            assert self.raven.events == []

    def test_invalid_client(self):
        extra_settings = {
            'SENTRY_CLIENT': 'raven.contrib.django.DjangoClient',  # default
        }
        # Should return fallback client (MockClient)
        client = get_client('nonexistent.and.invalid')

        # client should be valid, and the same as with the next call.
        assert client is get_client()

        with Settings(**extra_settings):
            assert isinstance(get_client(), DjangoClient)

    def test_transport_specification(self):
        extra_settings = {
            'SENTRY_TRANSPORT': 'raven.transport.HTTPTransport',
            'SENTRY_DSN': 'http://public:secret@example.com/1',
        }
        with Settings(**extra_settings):
            client = get_client(reset=True)
            assert type(client.remote.get_transport()) is HTTPTransport

    def test_response_error_id_middleware(self):
        # TODO: test with 500s
        with Settings(**{MIDDLEWARE_ATTR: [
                'raven.contrib.django.middleware.SentryResponseErrorIdMiddleware',
                'raven.contrib.django.middleware.Sentry404CatchMiddleware']}):
            resp = self.client.get('/non-existent-page')
            assert resp.status_code == 404
            headers = dict(resp.items())
            assert 'X-Sentry-ID' in headers
            assert len(self.raven.events) == 1
            event = self.raven.events.pop(0)
            assert event['event_id'] == headers['X-Sentry-ID']

    def test_get_client(self):
        assert get_client() == get_client()
        assert get_client('raven.base.Client').__class__ == Client
        assert get_client() == self.raven

        assert get_client('%s.%s' % (type(self.raven).__module__, type(self.raven).__name__)) == self.raven
        assert get_client() == self.raven

    def test_raw_post_data_partial_read(self):
        v = '{"foo": "bar"}'
        request = make_request()
        request.environ.update({
            'wsgi.input': StringIO(v + '\r\n\r\n'),
            'CONTENT_TYPE': 'application/octet-stream',
            'CONTENT_LENGTH': len(v),
        })
        request.read(1)

        self.raven.captureMessage(message='foo', request=request)

        assert len(self.raven.events) == 1
        event = self.raven.events.pop(0)

        assert 'request' in event
        http = event['request']
        assert http['method'] == 'POST'
        assert http['data'] == '<unavailable>'

    def test_read_post_data(self):
        request = make_request()
        request.POST = QueryDict("foo=bar&ham=spam")
        request.read(1)

        self.raven.captureMessage(message='foo', request=request)

        assert len(self.raven.events) == 1
        event = self.raven.events.pop(0)

        assert 'request' in event
        http = event['request']
        assert http['method'] == 'POST'
        assert http['data'] == {'foo': 'bar', 'ham': 'spam'}

    def test_request_capture(self):
        request = make_request()
        request.read(1)

        self.raven.captureMessage(message='foo', request=request)

        assert len(self.raven.events) == 1
        event = self.raven.events.pop(0)

        assert 'request' in event
        http = event['request']
        assert http['method'] == 'POST'
        assert http['data'] == '<unavailable>'
        assert 'headers' in http
        headers = http['headers']
        assert 'Content-Type' in headers, headers.keys()
        assert headers['Content-Type'] == 'text/html'
        env = http['env']
        assert 'SERVER_NAME' in env, env.keys()
        assert env['SERVER_NAME'] == 'testserver'
        assert 'SERVER_PORT' in env, env.keys()
        assert env['SERVER_PORT'] == '80'

    def test_marks_django_frames_correctly(self):
        self.assertRaises(TemplateSyntaxError, self.client.get, reverse('sentry-template-exc'))

        assert len(self.raven.events) == 1
        event = self.raven.events.pop(0)

        frames = event['exception']['values'][-1]['stacktrace']['frames']
        for frame in frames:
            if frame['module'].startswith('django.'):
                assert frame.get('in_app') is False

    def test_adds_site_to_tags(self):
        self.assertRaises(TemplateSyntaxError, self.client.get, reverse('sentry-template-exc'))

        assert len(self.raven.events) == 1
        event = self.raven.events.pop(0)

        tags = event['tags']
        assert 'site' in event['tags']
        assert tags['site'] == 'example.com'

    def test_adds_site_to_tags_fallback(self):
        with Settings(SITE_ID=12345):  # nonexistent site, should fallback to SITE_ID
            self.assertRaises(TemplateSyntaxError, self.client.get, reverse('sentry-template-exc'))

            assert len(self.raven.events) == 1
            event = self.raven.events.pop(0)

            tags = event['tags']
            assert 'site' in event['tags']
            assert tags['site'] == 12345

    def test_settings_site_overrides_contrib(self):
        self.raven.site = 'FOO'
        self.assertRaises(TemplateSyntaxError, self.client.get, reverse('sentry-template-exc'))

        assert len(self.raven.events) == 1
        event = self.raven.events.pop(0)

        tags = event['tags']
        assert 'site' in event['tags']
        assert tags['site'] == 'FOO'

    @mock.patch.object(WSGIRequest, 'build_absolute_uri')
    def test_suspicious_operation_in_build_absolute_uri(self, build_absolute_uri):
        build_absolute_uri.side_effect = SuspiciousOperation()
        request = make_request()
        request.META['HTTP_HOST'] = 'example.com'
        result = self.raven.get_data_from_request(request)
        build_absolute_uri.assert_called_once_with()
        assert 'request' in result
        assert result['request']['url'] == 'http://example.com/'


class DjangoTemplateTagTest(TestCase):
    @mock.patch('raven.contrib.django.DjangoClient.get_public_dsn')
    def test_sentry_public_dsn_no_args(self, get_public_dsn):
        sentry_public_dsn()
        get_public_dsn.assert_called_once_with(None)

    @mock.patch('raven.contrib.django.DjangoClient.get_public_dsn')
    def test_sentry_public_dsn_with_https(self, get_public_dsn):
        sentry_public_dsn('https')
        get_public_dsn.assert_called_once_with('https')


class DjangoLoggingTest(TestCase):
    def setUp(self):
        self.logger = logging.getLogger(__name__)
        self.raven = get_client()

    def test_request_kwarg(self):
        handler = SentryHandler()

        logger = self.logger
        logger.handlers = []
        logger.addHandler(handler)

        logger.error('This is a test error', extra={
            'request': WSGIRequest(environ={
                'wsgi.input': StringIO(),
                'REQUEST_METHOD': 'POST',
                'SERVER_NAME': 'testserver',
                'SERVER_PORT': '80',
                'CONTENT_TYPE': 'application/octet-stream',
                'ACCEPT': 'application/json',
            })
        })

        assert len(self.raven.events) == 1
        event = self.raven.events.pop(0)
        assert 'request' in event
        http = event['request']
        assert http['method'] == 'POST'

    def test_tags(self):
        tags = {'tag1': 'test'}
        handler = SentryHandler(tags=tags)

        logger = self.logger
        logger.handlers = []
        logger.addHandler(handler)

        logger.error('This is a test error')

        assert len(self.raven.events) == 1
        event = self.raven.events.pop(0)
        assert 'tags' in event
        # event['tags'] also contains some other data, like 'site'
        assert 'tag1' in event['tags']
        assert event['tags']['tag1'] == tags['tag1']


class CeleryIsolatedClientTest(TestCase):
    def setUp(self):
        self.client = CeleryClient(
            dsn='sync+http://public:secret@example.com/1'
        )

    @mock.patch('raven.contrib.django.celery.send_raw')
    def test_send_encoded(self, send_raw):
        self.client.send_encoded('foo')

        send_raw.delay.assert_called_once_with('foo')

    @mock.patch('raven.contrib.django.celery.send_raw')
    def test_without_eager(self, send_raw):
        """
        Integration test to ensure it propagates all the way down
        and calls delay on the task.
        """
        self.client.captureMessage(message='test')

        assert send_raw.delay.call_count == 1


class IsValidOriginTestCase(TestCase):
    def test_setting_empty(self):
        with Settings(SENTRY_ALLOW_ORIGIN=None):
            assert not is_valid_origin('http://example.com')

    def test_setting_all(self):
        with Settings(SENTRY_ALLOW_ORIGIN='*'):
            assert is_valid_origin('http://example.com')

    def test_setting_uri(self):
        with Settings(SENTRY_ALLOW_ORIGIN=['http://example.com']):
            assert is_valid_origin('http://example.com')

    def test_setting_regexp(self):
        with Settings(SENTRY_ALLOW_ORIGIN=[re.compile('https?\://(.*\.)?example\.com')]):
            assert is_valid_origin('http://example.com')


class ReportViewTest(TestCase):
    urls = 'raven.contrib.django.urls'

    def setUp(self):
        super(ReportViewTest, self).setUp()
        self.path = reverse('raven-report', args=['1'], urlconf=self.urls)

    @mock.patch('raven.contrib.django.views.is_valid_origin')
    def test_calls_is_valid_origin_with_header(self, is_valid_origin):
        with self.settings(ROOT_URLCONF=self.urls):
            self.client.post(self.path, HTTP_ORIGIN='http://example.com')
        is_valid_origin.assert_called_once_with('http://example.com')

    @mock.patch('raven.contrib.django.views.is_valid_origin')
    def test_calls_is_valid_origin_with_header_as_get(self, is_valid_origin):
        with self.settings(ROOT_URLCONF=self.urls):
            self.client.get(self.path, HTTP_ORIGIN='http://example.com')
        is_valid_origin.assert_called_once_with('http://example.com')

    @mock.patch('raven.contrib.django.views.is_valid_origin', mock.Mock(return_value=False))
    def test_fails_on_invalid_origin(self):
        with self.settings(ROOT_URLCONF=self.urls):
            resp = self.client.post(self.path, HTTP_ORIGIN='http://example.com')
        assert resp.status_code == 403

    @mock.patch('raven.contrib.django.views.is_valid_origin', mock.Mock(return_value=True))
    def test_options_call_sends_headers(self):
        with self.settings(ROOT_URLCONF=self.urls):
            resp = self.client.options(self.path, HTTP_ORIGIN='http://example.com')
        assert resp.status_code == 200
        assert resp['Access-Control-Allow-Origin'] == 'http://example.com'
        assert resp['Access-Control-Allow-Methods'], 'GET, POST == OPTIONS'

    @mock.patch('raven.contrib.django.views.is_valid_origin', mock.Mock(return_value=True))
    def test_missing_data(self):
        with self.settings(ROOT_URLCONF=self.urls):
            resp = self.client.post(self.path, HTTP_ORIGIN='http://example.com')
        assert resp.status_code == 400

    @mock.patch('raven.contrib.django.views.is_valid_origin', mock.Mock(return_value=True))
    def test_invalid_data(self):
        with self.settings(ROOT_URLCONF=self.urls):
            resp = self.client.post(self.path, HTTP_ORIGIN='http://example.com',
                data='[1', content_type='application/octet-stream')
        assert resp.status_code == 400

    @mock.patch('raven.contrib.django.views.is_valid_origin', mock.Mock(return_value=True))
    def test_sends_data(self):
        with self.settings(ROOT_URLCONF=self.urls):
            resp = self.client.post(self.path, HTTP_ORIGIN='http://example.com',
                data='{}', content_type='application/octet-stream')
        assert resp.status_code == 200
        event = client.events.pop(0)
        assert event == {'auth_header': None}

    @mock.patch('raven.contrib.django.views.is_valid_origin', mock.Mock(return_value=True))
    def test_sends_authorization_header(self):
        with self.settings(ROOT_URLCONF=self.urls):
            resp = self.client.post(self.path, HTTP_ORIGIN='http://example.com',
                HTTP_AUTHORIZATION='Sentry foo/bar', data='{}', content_type='application/octet-stream')
        assert resp.status_code == 200
        event = client.events.pop(0)
        assert event == {'auth_header': 'Sentry foo/bar'}

    @mock.patch('raven.contrib.django.views.is_valid_origin', mock.Mock(return_value=True))
    def test_sends_x_sentry_auth_header(self):
        with self.settings(ROOT_URLCONF=self.urls):
            resp = self.client.post(self.path, HTTP_ORIGIN='http://example.com',
                HTTP_X_SENTRY_AUTH='Sentry foo/bar', data='{}',
                content_type='application/octet-stream')
        assert resp.status_code == 200
        event = client.events.pop(0)
        assert event == {'auth_header': 'Sentry foo/bar'}


class PromiseSerializerTestCase(TestCase):
    def test_basic(self):
        from django.utils.functional import lazy

        obj = lazy(lambda: 'bar', text_type)()
        res = transform(obj)
        expected = "'bar'" if not PY2 else "u'bar'"
        assert res == expected

    def test_handles_gettext_lazy(self):
        from django.utils.functional import lazy

        def fake_gettext(to_translate):
            return 'Igpay Atinlay'

        fake_gettext_lazy = lazy(fake_gettext, text_type)

        result = transform(fake_gettext_lazy("something"))
        assert isinstance(result, string_types)
        expected = "'Igpay Atinlay'" if not PY2 else "u'Igpay Atinlay'"
        assert result == expected

    def test_real_gettext_lazy(self):
        d = {text_type('lazy_translation'): gettext_lazy(text_type('testing'))}
        key = "'lazy_translation'" if not PY2 else "u'lazy_translation'"
        value = "'testing'" if not PY2 else "u'testing'"
        assert transform(d) == {key: value}


class ModelInstanceSerializerTestCase(object):
    def test_basic(self, mytest_model):
        instance = mytest_model()

        result = transform(instance)
        assert isinstance(result, string_types)
        assert result == '<MyTestModel: MyTestModel object>'


class QuerySetSerializerTestCase(object):
    def test_basic(self, mytest_model):
        from django.db.models.query import QuerySet
        obj = QuerySet(model=mytest_model)

        result = transform(obj)
        assert isinstance(result, string_types)
        assert result == '<QuerySet: model=MyTestModel>'


class SentryExceptionHandlerTest(TestCase):
    @fixture
    def request(self):
        return make_request()

    @fixture
    def exc_info(self):
        return (ValueError, ValueError('lol world'), None)

    def setUp(self):
        super(SentryExceptionHandlerTest, self).setUp()
        self.client = get_client()
        self.handler = SentryDjangoHandler(self.client)

    @mock.patch.object(MockClient, 'captureException')
    @mock.patch('sys.exc_info')
    def test_does_capture_exception(self, exc_info, captureException):
        exc_info.return_value = self.exc_info
        self.handler.exception_handler(request=self.request)

        captureException.assert_called_once_with(exc_info=self.exc_info, request=self.request)

    @mock.patch.object(MockClient, 'send')
    @mock.patch('sys.exc_info')
    def test_does_exclude_filtered_types(self, exc_info, mock_send):
        exc_info.return_value = self.exc_info
        try:
            self.client.ignore_exceptions = set(['ValueError'])

            self.handler.exception_handler(request=self.request)
        finally:
            self.client.ignore_exceptions.clear()

        assert not mock_send.called

    @mock.patch.object(MockClient, 'send')
    @mock.patch('sys.exc_info')
    def test_ignore_exceptions_with_expression_match(self, exc_info, mock_send):
        exc_info.return_value = self.exc_info

        try:
            if not PY2:
                self.client.ignore_exceptions = set(['builtins.*'])
            else:
                self.client.ignore_exceptions = set(['exceptions.*'])
            self.handler.exception_handler(request=self.request)
        finally:
            self.client.ignore_exceptions.clear()

        assert not mock_send.called

    @mock.patch.object(MockClient, 'send')
    @mock.patch('sys.exc_info')
    def test_ignore_exceptions_with_module_match(self, exc_info, mock_send):
        exc_info.return_value = self.exc_info

        try:
            if not PY2:
                self.client.ignore_exceptions = set(['builtins.ValueError'])
            else:
                self.client.ignore_exceptions = set(['exceptions.ValueError'])
            self.handler.exception_handler(request=self.request)
        finally:
            self.client.ignore_exceptions.clear()

        assert not mock_send.called


class SQLHookTestCase(TestCase):
    def test_wrong_params(self):
        query = 'SELECT COUNT(*) FROM mytestmodel WHERE id = %s'
        args = ['foobar', 42]
        record_sql(None, None, None, None, query, args)
        crumbs = get_client().context.breadcrumbs.get_buffer()
        self.assertEqual(crumbs[-1]['message'], query)
