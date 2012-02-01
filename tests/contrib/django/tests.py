# -*- coding: utf-8 -*-

from __future__ import absolute_import

import mock
import datetime
import logging
from celery.tests.utils import with_eager_tasks
from StringIO import StringIO

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.signals import got_request_exception
from django.core.handlers.wsgi import WSGIRequest
from django.template import TemplateSyntaxError
from django.test import TestCase

from raven.base import Client
from raven.contrib.django import DjangoClient
from raven.contrib.django.celery import CeleryClient
from raven.contrib.django.handlers import SentryHandler
from raven.contrib.django.models import get_client
from raven.contrib.django.middleware.wsgi import Sentry

from django.test.client import Client as TestClient, ClientHandler as TestClientHandler

settings.SENTRY_CLIENT = 'tests.contrib.django.tests.TempStoreClient'


class MockClientHandler(TestClientHandler):
    def __call__(self, environ, start_response=[]):
        # this pretends doesnt require start_response
        return super(MockClientHandler, self).__call__(environ)


class MockSentryMiddleware(Sentry):
    def __call__(self, environ, start_response=[]):
        # this pretends doesnt require start_response
        return list(super(MockSentryMiddleware, self).__call__(environ, start_response))


class TempStoreClient(DjangoClient):
    def __init__(self, *args, **kwargs):
        self.events = []
        super(TempStoreClient, self).__init__(*args, **kwargs)

    def send(self, **kwargs):
        self.events.append(kwargs)


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
        for k, v in self.overrides.iteritems():
            self._orig[k] = getattr(settings, k, self.NotDefined)
            setattr(settings, k, v)

    def __exit__(self, exc_type, exc_value, traceback):
        for k, v in self._orig.iteritems():
            if v is self.NotDefined:
                delattr(settings, k)
            else:
                setattr(settings, k, v)


class DjangoClientTest(TestCase):
    ## Fixture setup/teardown
    urls = 'tests.contrib.django.urls'

    def setUp(self):
        self.raven = get_client()

    def test_basic(self):
        self.raven.capture('Message', message='foo')
        self.assertEquals(len(self.raven.events), 1)
        event = self.raven.events.pop(0)
        self.assertTrue('sentry.interfaces.Message' in event)
        message = event['sentry.interfaces.Message']
        self.assertEquals(message['message'], 'foo')
        self.assertEquals(event['level'], logging.ERROR)
        self.assertEquals(event['message'], 'foo')
        self.assertEquals(type(event['timestamp']), datetime.datetime)

    def test_signal_integration(self):
        try:
            int('hello')
        except:
            got_request_exception.send(sender=self.__class__, request=None)
        else:
            self.fail('Expected an exception.')

        self.assertEquals(len(self.raven.events), 1)
        event = self.raven.events.pop(0)
        self.assertTrue('sentry.interfaces.Exception' in event)
        exc = event['sentry.interfaces.Exception']
        self.assertEquals(exc['type'], 'ValueError')
        self.assertEquals(exc['value'], u"invalid literal for int() with base 10: 'hello'")
        self.assertEquals(event['level'], logging.ERROR)
        self.assertEquals(event['message'], u"ValueError: invalid literal for int() with base 10: 'hello'")
        self.assertEquals(event['culprit'], 'tests.contrib.django.tests.test_signal_integration')

    def test_view_exception(self):
        self.assertRaises(Exception, self.client.get, reverse('sentry-raise-exc'))

        self.assertEquals(len(self.raven.events), 1)
        event = self.raven.events.pop(0)
        self.assertTrue('sentry.interfaces.Exception' in event)
        exc = event['sentry.interfaces.Exception']
        self.assertEquals(exc['type'], 'Exception')
        self.assertEquals(exc['value'], 'view exception')
        self.assertEquals(event['level'], logging.ERROR)
        self.assertEquals(event['message'], 'Exception: view exception')
        self.assertEquals(event['culprit'], 'tests.contrib.django.views.raise_exc')

    def test_user_info(self):
        user = User(username='admin', email='admin@example.com')
        user.set_password('admin')
        user.save()

        self.assertRaises(Exception, self.client.get, reverse('sentry-raise-exc'))

        self.assertEquals(len(self.raven.events), 1)
        event = self.raven.events.pop(0)
        self.assertTrue('sentry.interfaces.User' in event)
        user_info = event['sentry.interfaces.User']
        self.assertTrue('is_authenticated' in user_info)
        self.assertFalse(user_info['is_authenticated'])
        self.assertFalse('username' in user_info)
        self.assertFalse('email' in user_info)

        self.assertTrue(self.client.login(username='admin', password='admin'))

        self.assertRaises(Exception, self.client.get, reverse('sentry-raise-exc'))

        self.assertEquals(len(self.raven.events), 1)
        event = self.raven.events.pop(0)
        self.assertTrue('sentry.interfaces.User' in event)
        user_info = event['sentry.interfaces.User']
        self.assertTrue('is_authenticated' in user_info)
        self.assertTrue(user_info['is_authenticated'])
        self.assertTrue('username' in user_info)
        self.assertEquals(user_info['username'], 'admin')
        self.assertTrue('email' in user_info)
        self.assertEquals(user_info['email'], 'admin@example.com')

    def test_request_middleware_exception(self):
        with Settings(MIDDLEWARE_CLASSES=['tests.contrib.django.middleware.BrokenRequestMiddleware']):
            self.assertRaises(ImportError, self.client.get, reverse('sentry-raise-exc'))

            self.assertEquals(len(self.raven.events), 1)
            event = self.raven.events.pop(0)

            self.assertTrue('sentry.interfaces.Exception' in event)
            exc = event['sentry.interfaces.Exception']
            self.assertEquals(exc['type'], 'ImportError')
            self.assertEquals(exc['value'], 'request')
            self.assertEquals(event['level'], logging.ERROR)
            self.assertEquals(event['message'], 'ImportError: request')
            self.assertEquals(event['culprit'], 'tests.contrib.django.middleware.process_request')

    def test_response_middlware_exception(self):
        with Settings(MIDDLEWARE_CLASSES=['tests.contrib.django.middleware.BrokenResponseMiddleware']):
            self.assertRaises(ImportError, self.client.get, reverse('sentry-no-error'))

            self.assertEquals(len(self.raven.events), 1)
            event = self.raven.events.pop(0)

            self.assertTrue('sentry.interfaces.Exception' in event)
            exc = event['sentry.interfaces.Exception']
            self.assertEquals(exc['type'], 'ImportError')
            self.assertEquals(exc['value'], 'response')
            self.assertEquals(event['level'], logging.ERROR)
            self.assertEquals(event['message'], 'ImportError: response')
            self.assertEquals(event['culprit'], 'tests.contrib.django.middleware.process_response')

    def test_broken_500_handler_with_middleware(self):
        with Settings(BREAK_THAT_500=True):
            client = TestClient(REMOTE_ADDR='127.0.0.1')
            client.handler = MockSentryMiddleware(MockClientHandler())

            self.assertRaises(Exception, client.get, reverse('sentry-raise-exc'))

            self.assertEquals(len(self.raven.events), 2)
            event = self.raven.events.pop(0)

            self.assertTrue('sentry.interfaces.Exception' in event)
            exc = event['sentry.interfaces.Exception']
            self.assertEquals(exc['type'], 'Exception')
            self.assertEquals(exc['value'], 'view exception')
            self.assertEquals(event['level'], logging.ERROR)
            self.assertEquals(event['message'], 'Exception: view exception')
            self.assertEquals(event['culprit'], 'tests.contrib.django.views.raise_exc')

            event = self.raven.events.pop(0)

            self.assertTrue('sentry.interfaces.Exception' in event)
            exc = event['sentry.interfaces.Exception']
            self.assertEquals(exc['type'], 'ValueError')
            self.assertEquals(exc['value'], 'handler500')
            self.assertEquals(event['level'], logging.ERROR)
            self.assertEquals(event['message'], 'ValueError: handler500')
            self.assertEquals(event['culprit'], 'tests.contrib.django.urls.handler500')

    def test_view_middleware_exception(self):
        with Settings(MIDDLEWARE_CLASSES=['tests.contrib.django.middleware.BrokenViewMiddleware']):
            self.assertRaises(ImportError, self.client.get, reverse('sentry-raise-exc'))

            self.assertEquals(len(self.raven.events), 1)
            event = self.raven.events.pop(0)

            self.assertTrue('sentry.interfaces.Exception' in event)
            exc = event['sentry.interfaces.Exception']
            self.assertEquals(exc['type'], 'ImportError')
            self.assertEquals(exc['value'], 'view')
            self.assertEquals(event['level'], logging.ERROR)
            self.assertEquals(event['message'], 'ImportError: view')
            self.assertEquals(event['culprit'], 'tests.contrib.django.middleware.process_view')

    def test_exclude_modules_view(self):
        exclude_paths = self.raven.exclude_paths
        self.raven.exclude_paths = ['tests.views.decorated_raise_exc']
        self.assertRaises(Exception, self.client.get, reverse('sentry-raise-exc-decor'))

        self.assertEquals(len(self.raven.events), 1)
        event = self.raven.events.pop(0)

        self.assertEquals(event['culprit'], 'tests.contrib.django.views.raise_exc')
        self.raven.exclude_paths = exclude_paths

    def test_include_modules(self):
        include_paths = self.raven.include_paths
        self.raven.include_paths = ['django.shortcuts.get_object_or_404']

        self.assertRaises(Exception, self.client.get, reverse('sentry-django-exc'))

        self.assertEquals(len(self.raven.events), 1)
        event = self.raven.events.pop(0)

        self.assertEquals(event['culprit'], 'django.shortcuts.get_object_or_404')
        self.raven.include_paths = include_paths

    def test_template_name_as_view(self):
        self.assertRaises(TemplateSyntaxError, self.client.get, reverse('sentry-template-exc'))

        self.assertEquals(len(self.raven.events), 1)
        event = self.raven.events.pop(0)

        self.assertEquals(event['culprit'], 'error.html')

    # def test_request_in_logging(self):
    #     resp = self.client.get(reverse('sentry-log-request-exc'))
    #     self.assertEquals(resp.status_code, 200)

    #     self.assertEquals(len(self.raven.events), 1)
    #     event = self.raven.events.pop(0)

    #     self.assertEquals(event['culprit'], 'tests.contrib.django.views.logging_request_exc')
    #     self.assertEquals(event['data']['META']['REMOTE_ADDR'], '127.0.0.1')

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

        self.assertEquals(len(self.raven.events), 1)
        event = self.raven.events.pop(0)

        self.assertEquals(event['message'], 'test')

    def test_404_middleware(self):
        with Settings(MIDDLEWARE_CLASSES=['raven.contrib.django.middleware.Sentry404CatchMiddleware']):
            resp = self.client.get('/non-existant-page')
            self.assertEquals(resp.status_code, 404)

            self.assertEquals(len(self.raven.events), 1)
            event = self.raven.events.pop(0)

            self.assertEquals(event['level'], logging.INFO)
            self.assertEquals(event['logger'], 'http404')

            self.assertTrue('sentry.interfaces.Http' in event)
            http = event['sentry.interfaces.Http']
            self.assertEquals(http['url'], u'http://testserver/non-existant-page')
            self.assertEquals(http['method'], 'GET')
            self.assertEquals(http['query_string'], '')
            self.assertEquals(http['data'], {})

    def test_response_error_id_middleware(self):
        # TODO: test with 500s
        with Settings(MIDDLEWARE_CLASSES=['raven.contrib.django.middleware.SentryResponseErrorIdMiddleware', 'raven.contrib.django.middleware.Sentry404CatchMiddleware']):
            resp = self.client.get('/non-existant-page')
            self.assertEquals(resp.status_code, 404)
            headers = dict(resp.items())
            self.assertTrue('X-Sentry-ID' in headers)
            self.assertEquals(len(self.raven.events), 1)
            event = self.raven.events.pop(0)
            self.assertEquals('$'.join([event['event_id'], event['checksum']]), headers['X-Sentry-ID'])

    def test_get_client(self):
        self.assertEquals(get_client(), get_client())
        self.assertEquals(get_client('raven.base.Client').__class__, Client)
        self.assertEquals(get_client(), self.raven)

        self.assertEquals(get_client('%s.%s' % (self.raven.__class__.__module__, self.raven.__class__.__name__)), self.raven)
        self.assertEquals(get_client(), self.raven)

    def test_raw_post_data_partial_read(self):
        # This test only applies to Django 1.3+
        v = '{"foo": "bar"}'
        request = WSGIRequest(environ={
            'wsgi.input': StringIO(v + '\r\n\r\n'),
            'REQUEST_METHOD': 'POST',
            'SERVER_NAME': 'testserver',
            'SERVER_PORT': '80',
            'CONTENT_TYPE': 'application/octet-stream',
            'CONTENT_LENGTH': len(v),
            'ACCEPT': 'application/json',
        })
        request.read(1)

        self.raven.capture('Message', message='foo', request=request)

        self.assertEquals(len(self.raven.events), 1)
        event = self.raven.events.pop(0)

        self.assertTrue('sentry.interfaces.Http' in event)
        http = event['sentry.interfaces.Http']
        self.assertEquals(http['method'], 'POST')
        self.assertEquals(http['data'], '<unavailable>')

    def test_request_capture(self):
        request = WSGIRequest(environ={
            'wsgi.input': StringIO(),
            'REQUEST_METHOD': 'POST',
            'SERVER_NAME': 'testserver',
            'SERVER_PORT': '80',
            'CONTENT_TYPE': 'text/html',
            'ACCEPT': 'text/html',
        })
        request.read(1)

        self.raven.capture('Message', message='foo', request=request)

        self.assertEquals(len(self.raven.events), 1)
        event = self.raven.events.pop(0)

        self.assertTrue('sentry.interfaces.Http' in event)
        http = event['sentry.interfaces.Http']
        self.assertEquals(http['method'], 'POST')
        self.assertEquals(http['data'], '<unavailable>')
        self.assertTrue('headers' in http)
        headers = http['headers']
        self.assertTrue('Content-Type' in headers, headers.keys())
        self.assertEquals(headers['Content-Type'], 'text/html')
        env = http['env']
        self.assertTrue('SERVER_NAME' in env, env.keys())
        self.assertEquals(env['SERVER_NAME'], 'testserver')
        self.assertTrue('SERVER_PORT' in env, env.keys())
        self.assertEquals(env['SERVER_PORT'], '80')


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

        self.assertEquals(len(self.raven.events), 1)
        event = self.raven.events.pop(0)
        self.assertTrue('sentry.interfaces.Http' in event)
        http = event['sentry.interfaces.Http']
        self.assertEquals(http['method'], 'POST')


class CeleryIsolatedClientTest(TestCase):
    def setUp(self):
        self.client = CeleryClient(
            servers=['http://example.com'],
            public_key='public',
            secret_key='secret',
        )

    @mock.patch('raven.contrib.django.celery.CeleryClient.send_raw')
    def test_send_encoded(self, send_raw):
        self.client.send_encoded('foo')

        send_raw.delay.assert_called_once_with('foo')

    @mock.patch('raven.contrib.django.celery.CeleryClient.send_raw')
    def test_without_eager(self, send_raw):
        """
        Integration test to ensure it propagates all the way down
        and calls delay on the task.
        """
        self.client.capture('Message', message='test')

        self.assertEquals(send_raw.delay.call_count, 1)

    @with_eager_tasks
    @mock.patch('raven.contrib.django.DjangoClient.send_encoded')
    def test_with_eager(self, send_encoded):
        """
        Integration test to ensure it propagates all the way down
        and calls the parent client's send_encoded method.
        """
        self.client.capture('Message', message='test')

        self.assertEquals(send_encoded.call_count, 1)


class CeleryIntegratedClientTest(TestCase):
    def setUp(self):
        self.client = CeleryClient()

    @mock.patch('raven.contrib.django.celery.CeleryClient.send_raw_integrated')
    def test_send_encoded(self, send_raw):
        self.client.send_integrated('foo')

        send_raw.delay.assert_called_once_with('foo')

    @mock.patch('raven.contrib.django.celery.CeleryClient.send_raw_integrated')
    def test_without_eager(self, send_raw):
        """
        Integration test to ensure it propagates all the way down
        and calls delay on the task.
        """
        self.client.capture('Message', message='test')

        self.assertEquals(send_raw.delay.call_count, 1)

    @with_eager_tasks
    @mock.patch('raven.contrib.django.DjangoClient.send_encoded')
    def test_with_eager(self, send_encoded):
        """
        Integration test to ensure it propagates all the way down
        and calls the parent client's send_encoded method.
        """
        self.client.capture('Message', message='test')

        self.assertEquals(send_encoded.call_count, 1)
