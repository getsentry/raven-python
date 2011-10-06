# -*- coding: utf-8 -*-

from __future__ import absolute_import

from django.conf import settings as django_settings

if not django_settings.configured:
    django_settings.configure(
        DATABASE_ENGINE='sqlite3',
        DATABASES={
            'default': {
                'ENGINE': 'sqlite3',
                'TEST_NAME': 'sentry_tests.db',
            },
        },
        # HACK: this fixes our threaded runserver remote tests
        # DATABASE_NAME='test_sentry',
        TEST_DATABASE_NAME='sentry_tests.db',
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.admin',
            'django.contrib.sessions',
            'django.contrib.sites',

            # Included to fix Disqus' test Django which solves IntegrityMessage case
            'django.contrib.contenttypes',

            'south',
            'djcelery', # celery client
            'haystack',

            'sentry_client.contrib.django',
        ],
        ROOT_URLCONF='',
        DEBUG=False,
        SITE_ID=1,
        BROKER_HOST="localhost",
        BROKER_PORT=5672,
        BROKER_USER="guest",
        BROKER_PASSWORD="guest",
        BROKER_VHOST="/",
        CELERY_ALWAYS_EAGER=True,
        TEMPLATE_DEBUG=True,
        HAYSTACK_SITECONF='sentry.search_indexes',
        HAYSTACK_SEARCH_ENGINE='whoosh',
    )
    import djcelery
    djcelery.setup_loader()

from unittest2 import TestCase

from django.http import HttpRequest
from sentry_client.contrib.django.models import sentry_exception_handler

import logging

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.signals import got_request_exception
from django.template import TemplateSyntaxError
from django.utils.encoding import smart_unicode

from sentry_client.base import SentryClient
from sentry_client.contrib.django.models import get_client
from sentry_client.conf import settings

class SentryTest(TestCase):
    ## Fixture setup/teardown
    def setUp(self):
        self._middleware = django_settings.MIDDLEWARE_CLASSES
        self._handlers = None
        self._level = None
        self.logger = logging.getLogger('sentry')
        self.logger.addHandler(logging.StreamHandler())

    def tearDown(self):
        self.tearDownHandler()
        django_settings.MIDDLEWARE_CLASSES = self._middleware

    def setUpHandler(self):
        self.tearDownHandler()

        logger = logging.getLogger()
        self._handlers = logger.handlers
        self._level = logger.level

        for h in self._handlers:
            # TODO: fix this, for now, I don't care.
            logger.removeHandler(h)

        logger.setLevel(logging.DEBUG)
        sentry_handler = SentryHandler(SentryClient())
        logger.addHandler(sentry_handler)

    def tearDownHandler(self):
        if self._handlers is None:
            return

        logger = logging.getLogger()
        logger.removeHandler(logger.handlers[0])
        for h in self._handlers:
            logger.addHandler(h)

        logger.setLevel(self._level)
        self._handlers = None


    ## Tests

    def test_logger(self):
        logger = logging.getLogger()

        self.setUpHandler()

        logger.error('This is a test error')
        self.assertEquals(Message.objects.count(), 1)
        self.assertEquals(GroupedMessage.objects.count(), 1)
        last = Message.objects.get()
        self.assertEquals(last.logger, 'root')
        self.assertEquals(last.level, logging.ERROR)
        self.assertEquals(last.message, 'This is a test error')

        logger.warning('This is a test warning')
        self.assertEquals(Message.objects.count(), 2)
        self.assertEquals(GroupedMessage.objects.count(), 2)
        last = Message.objects.all().order_by('-id')[0:1].get()
        self.assertEquals(last.logger, 'root')
        self.assertEquals(last.level, logging.WARNING)
        self.assertEquals(last.message, 'This is a test warning')

        logger.error('This is a test error')
        self.assertEquals(Message.objects.count(), 3)
        self.assertEquals(GroupedMessage.objects.count(), 2)
        last = Message.objects.all().order_by('-id')[0:1].get()
        self.assertEquals(last.logger, 'root')
        self.assertEquals(last.level, logging.ERROR)
        self.assertEquals(last.message, 'This is a test error')

        logger = logging.getLogger('test')
        logger.info('This is a test info')
        self.assertEquals(Message.objects.count(), 4)
        self.assertEquals(GroupedMessage.objects.count(), 3)
        last = Message.objects.all().order_by('-id')[0:1].get()
        self.assertEquals(last.logger, 'test')
        self.assertEquals(last.level, logging.INFO)
        self.assertEquals(last.message, 'This is a test info')

        logger.info('This is a test info with a url', extra=dict(url='http://example.com'))
        self.assertEquals(Message.objects.count(), 5)
        self.assertEquals(GroupedMessage.objects.count(), 4)
        last = Message.objects.all().order_by('-id')[0:1].get()
        self.assertEquals(last.url, 'http://example.com')

        try:
            raise ValueError('This is a test ValueError')
        except ValueError:
            logger.info('This is a test info with an exception', exc_info=True)

        self.assertEquals(Message.objects.count(), 6)
        self.assertEquals(GroupedMessage.objects.count(), 5)
        last = Message.objects.all().order_by('-id')[0:1].get()
        self.assertEquals(last.class_name, 'ValueError')
        self.assertEquals(last.message, 'This is a test info with an exception')
        self.assertTrue('__sentry__' in last.data)
        self.assertTrue('exception' in last.data['__sentry__'])
        self.assertTrue('frames' in last.data['__sentry__'])

        # test stacks
        logger.info('This is a test of stacks', extra={'stack': True})
        self.assertEquals(Message.objects.count(), 7)
        self.assertEquals(GroupedMessage.objects.count(), 6)
        last = Message.objects.all().order_by('-id')[0:1].get()
        self.assertEquals(last.view, 'tests.tests.test_logger')
        self.assertEquals(last.class_name, None)
        self.assertEquals(last.message, 'This is a test of stacks')
        self.assertTrue('__sentry__' in last.data)
        self.assertTrue('frames' in last.data['__sentry__'])

        # test no stacks
        logger.info('This is a test of no stacks', extra={'stack': False})
        self.assertEquals(Message.objects.count(), 8)
        self.assertEquals(GroupedMessage.objects.count(), 7)
        last = Message.objects.all().order_by('-id')[0:1].get()
        self.assertEquals(last.class_name, None)
        self.assertEquals(last.message, 'This is a test of no stacks')
        self.assertTrue('__sentry__' in last.data)
        self.assertFalse('frames' in last.data['__sentry__'])

        self.tearDownHandler()

    def test_incorrect_unicode(self):
        self.setUpHandler()

        cnt = Message.objects.count()
        value = 'רונית מגן'

        message_id = get_client().create_from_text(value)
        error = Message.objects.get(message_id=message_id)

        self.assertEquals(Message.objects.count(), cnt+1)
        self.assertEquals(error.message, u'רונית מגן')

        logging.info(value)
        self.assertEquals(Message.objects.count(), cnt+2)

        x = TestModel.objects.create(data={'value': value})
        logging.warn(x)
        self.assertEquals(Message.objects.count(), cnt+3)

        try:
            raise SyntaxMessage(value)
        except Exception, exc:
            logging.exception(exc)
            logging.info('test', exc_info=True)
        self.assertEquals(Message.objects.count(), cnt+5)

        self.tearDownHandler()

    def test_correct_unicode(self):
        self.setUpHandler()

        cnt = Message.objects.count()
        value = 'רונית מגן'.decode('utf-8')

        message_id = get_client().create_from_text(value)
        error = Message.objects.get(message_id=message_id)

        self.assertEquals(Message.objects.count(), cnt+1)
        self.assertEquals(error.message, value)

        logging.info(value)
        self.assertEquals(Message.objects.count(), cnt+2)

        x = TestModel.objects.create(data={'value': value})
        logging.warn(x)
        self.assertEquals(Message.objects.count(), cnt+3)

        try:
            raise SyntaxMessage(value)
        except Exception, exc:
            logging.exception(exc)
            logging.info('test', exc_info=True)
        self.assertEquals(Message.objects.count(), cnt+5)

        self.tearDownHandler()

    def test_long_urls(self):
        # Fix: #6 solves URLs > 200 characters
        message_id = get_client().create_from_text('hello world', url='a'*210)
        error = Message.objects.get(message_id=message_id)

        self.assertEquals(error.url, 'a'*200)
        self.assertEquals(error.data['url'], 'a'*210)

    def test_signals(self):
        try:
            Message.objects.get(id=999999999)
        except Message.DoesNotExist, exc:
            got_request_exception.send(sender=self.__class__, request=None)
        else:
            self.fail('Expected an exception.')

        self.assertEquals(Message.objects.count(), 1)
        self.assertEquals(GroupedMessage.objects.count(), 1)
        last = Message.objects.get()
        self.assertEquals(last.logger, 'root')
        self.assertEquals(last.class_name, 'DoesNotExist')
        self.assertEquals(last.level, logging.ERROR)
        self.assertEquals(last.message, smart_unicode(exc))

    def test_signals_without_request(self):
        try:
            Message.objects.get(id=999999999)
        except Message.DoesNotExist, exc:
            got_request_exception.send(sender=self.__class__, request=None)
        else:
            self.fail('Expected an exception.')

        self.assertEquals(Message.objects.count(), 1)
        self.assertEquals(GroupedMessage.objects.count(), 1)
        last = Message.objects.get()
        self.assertEquals(last.logger, 'root')
        self.assertEquals(last.class_name, 'DoesNotExist')
        self.assertEquals(last.level, logging.ERROR)
        self.assertEquals(last.message, smart_unicode(exc))

    def test_database_message(self):
        from django.db import connection

        try:
            cursor = connection.cursor()
            cursor.execute("select foo")
        except:
            got_request_exception.send(sender=self.__class__)

        self.assertEquals(Message.objects.count(), 1)
        self.assertEquals(GroupedMessage.objects.count(), 1)

    def test_integrity_message(self):
        DuplicateKeyModel.objects.create()
        try:
            DuplicateKeyModel.objects.create()
        except:
            got_request_exception.send(sender=self.__class__)
        else:
            self.fail('Excepted an IntegrityMessage to be raised.')

        self.assertEquals(Message.objects.count(), 1)
        self.assertEquals(GroupedMessage.objects.count(), 1)

    def test_view_exception(self):
        self.assertRaises(Exception, self.client.get, reverse('sentry-raise-exc'))

        self.assertEquals(GroupedMessage.objects.count(), 1)
        self.assertEquals(Message.objects.count(), 1)
        last = Message.objects.get()
        self.assertEquals(last.logger, 'root')
        self.assertEquals(last.class_name, 'Exception')
        self.assertEquals(last.level, logging.ERROR)
        self.assertEquals(last.message, 'view exception')
        self.assertEquals(last.view, 'tests.views.raise_exc')

    def test_user_info(self):
        user = User(username='admin', email='admin@example.com')
        user.set_password('admin')
        user.save()

        self.assertRaises(Exception, self.client.get, reverse('sentry-raise-exc'))

        self.assertEquals(GroupedMessage.objects.count(), 1)
        self.assertEquals(Message.objects.count(), 1)
        last = Message.objects.get()
        self.assertTrue('user' in last.data['__sentry__'])
        user_info = last.data['__sentry__']['user']
        self.assertTrue('is_authenticated' in user_info)
        self.assertFalse(user_info['is_authenticated'])
        self.assertFalse('username' in user_info)
        self.assertFalse('email' in user_info)

        self.assertTrue(self.client.login(username='admin', password='admin'))

        self.assertRaises(Exception, self.client.get, reverse('sentry-raise-exc'))

        self.assertEquals(GroupedMessage.objects.count(), 1)
        self.assertEquals(Message.objects.count(), 2)
        last = Message.objects.order_by('-id')[0]
        self.assertTrue('user' in last.data['__sentry__'])
        user_info = last.data['__sentry__']['user']
        self.assertTrue('is_authenticated' in user_info)
        self.assertTrue(user_info['is_authenticated'])
        self.assertTrue('username' in user_info)
        self.assertEquals(user_info['username'], 'admin')
        self.assertTrue('email' in user_info)
        self.assertEquals(user_info['email'], 'admin@example.com')

    def test_request_middleware_exception(self):
        orig = list(django_settings.MIDDLEWARE_CLASSES)
        django_settings.MIDDLEWARE_CLASSES = orig + ['tests.middleware.BrokenRequestMiddleware',]

        self.assertRaises(ImportError, self.client.get, reverse('sentry'))
        self.assertEquals(Message.objects.count(), 1)
        self.assertEquals(GroupedMessage.objects.count(), 1)
        last = Message.objects.get()
        self.assertEquals(last.logger, 'root')
        self.assertEquals(last.class_name, 'ImportError')
        self.assertEquals(last.level, logging.ERROR)
        self.assertEquals(last.message, 'request')
        self.assertEquals(last.view, 'tests.middleware.process_request')

        django_settings.MIDDLEWARE_CLASSES = orig

    # XXX: Django doesn't handle response middleware exceptions (yet)
    # def test_response_middlware_exception(self):
    #     orig = list(django_settings.MIDDLEWARE_CLASSES)
    #     django_settings.MIDDLEWARE_CLASSES = orig + ['tests.middleware.BrokenResponseMiddleware',]
    #
    #     self.assertRaises(ImportError, self.client.get, reverse('sentry'))
    #     self.assertEquals(Message.objects.count(), 1)
    #     self.assertEquals(GroupedMessage.objects.count(), 1)
    #     last = Message.objects.get()
    #     self.assertEquals(last.logger, 'root')
    #     self.assertEquals(last.class_name, 'ImportError')
    #     self.assertEquals(last.level, logging.ERROR)
    #     self.assertEquals(last.message, 'response')
    #     self.assertEquals(last.view, 'tests.middleware.process_response')
    #
    #     django_settings.MIDDLEWARE_CLASSES = orig

    def test_view_middleware_exception(self):
        orig = list(django_settings.MIDDLEWARE_CLASSES)
        django_settings.MIDDLEWARE_CLASSES = orig + ['tests.middleware.BrokenViewMiddleware',]

        self.assertRaises(ImportError, self.client.get, reverse('sentry'))
        self.assertEquals(Message.objects.count(), 1)
        self.assertEquals(GroupedMessage.objects.count(), 1)
        last = Message.objects.get()
        self.assertEquals(last.logger, 'root')
        self.assertEquals(last.class_name, 'ImportError')
        self.assertEquals(last.level, logging.ERROR)
        self.assertEquals(last.message, 'view')
        self.assertEquals(last.view, 'tests.middleware.process_view')

        django_settings.MIDDLEWARE_CLASSES = orig

    def test_setting_name(self):
        orig_name = settings.NAME
        orig_site = settings.SITE
        settings.NAME = 'foo'
        settings.SITE = 'bar'

        self.assertRaises(Exception, self.client.get, reverse('sentry-raise-exc'))

        self.assertEquals(Message.objects.count(), 1)
        self.assertEquals(GroupedMessage.objects.count(), 1)
        last = Message.objects.get()
        self.assertEquals(last.logger, 'root')
        self.assertEquals(last.class_name, 'Exception')
        self.assertEquals(last.level, logging.ERROR)
        self.assertEquals(last.message, 'view exception')
        self.assertEquals(last.server_name, 'foo')
        self.assertEquals(last.site, 'bar')
        self.assertEquals(last.view, 'tests.views.raise_exc')

        settings.NAME = orig_name
        settings.SITE = orig_site

    def test_exclusion_view_path(self):
        try: Message.objects.get(pk=1341324)
        except: get_client().create_from_exception()

        last = Message.objects.get()

        self.assertEquals(last.view, 'tests.tests.test_exclusion_view_path')

    def test_best_guess_view(self):
        settings.EXCLUDE_PATHS = ['tests.tests']

        try: Message.objects.get(pk=1341324)
        except: get_client().create_from_exception()

        last = Message.objects.get()

        self.assertEquals(last.view, 'tests.tests.test_best_guess_view')

        settings.EXCLUDE_PATHS = []

    def test_exclude_modules_view(self):
        settings.EXCLUDE_PATHS = ['tests.views.decorated_raise_exc']

        self.assertRaises(Exception, self.client.get, reverse('sentry-raise-exc-decor'))

        last = Message.objects.get()

        self.assertEquals(last.view, 'tests.views.raise_exc')

        settings.EXCLUDE_PATHS = []

    def test_varying_messages(self):
        self.assertRaises(Exception, self.client.get, reverse('sentry-raise-exc') + '?message=foo')
        self.assertRaises(Exception, self.client.get, reverse('sentry-raise-exc') + '?message=bar')
        self.assertRaises(Exception, self.client.get, reverse('sentry-raise-exc') + '?message=gra')

        self.assertEquals(GroupedMessage.objects.count(), 1)

    def test_include_modules(self):
        settings.INCLUDE_PATHS = ['django.shortcuts.get_object_or_404']

        self.assertRaises(Exception, self.client.get, reverse('sentry-django-exc'))

        last = Message.objects.get()

        self.assertEquals(last.view, 'django.shortcuts.get_object_or_404')

        settings.INCLUDE_PATHS = []

    def test_template_name_as_view(self):
        self.assertRaises(TemplateSyntaxError, self.client.get, reverse('sentry-template-exc'))

        last = Message.objects.get()

        self.assertEquals(last.view, 'sentry-tests/error.html')

    def test_request_in_logging(self):
        resp = self.client.get(reverse('sentry-log-request-exc'))
        self.assertEquals(resp.status_code, 200)

        last = Message.objects.get()

        self.assertEquals(last.view, 'tests.views.logging_request_exc')
        self.assertEquals(last.data['META']['REMOTE_ADDR'], '127.0.0.1')

    def test_create_from_record_none_exc_info(self):
        # sys.exc_info can return (None, None, None) if no exception is being
        # handled anywhere on the stack. See:
        #  http://docs.python.org/library/sys.html#sys.exc_info
        client = get_client()
        record = logging.LogRecord(
            'foo',
            logging.INFO,
            pathname=None,
            lineno=None,
            msg='test',
            args=(),
            exc_info=(None, None, None),
        )
        message_id = client.create_from_record(record)
        message = Message.objects.get(message_id=message_id)

        self.assertEquals('test', message.message)

    def test_versions(self):
        import sentry
        resp = self.client.get(reverse('sentry-log-request-exc'))
        self.assertEquals(resp.status_code, 200)

        self.assertEquals(Message.objects.count(), 1)
        self.assertEquals(GroupedMessage.objects.count(), 1)

        last = Message.objects.get()
        self.assertTrue('versions' in last.data['__sentry__'], last.data['__sentry__'])
        self.assertTrue('sentry' in last.data['__sentry__']['versions'], last.data['__sentry__'])
        self.assertEquals(last.data['__sentry__']['versions']['sentry'], sentry.VERSION)
        self.assertTrue('module' in last.data['__sentry__'], last.data['__sentry__'])
        self.assertEquals(last.data['__sentry__']['module'], 'tests')
        self.assertTrue('version' in last.data['__sentry__'], last.data['__sentry__'])
        self.assertEquals(last.data['__sentry__']['version'], '1.0')

        last = GroupedMessage.objects.get()
        self.assertTrue('module' in last.data)
        self.assertEquals(last.data['module'], 'tests')
        self.assertTrue('version' in last.data)
        self.assertEquals(last.data['version'], '1.0')

    def test_404_middleware(self):
        existing = django_settings.MIDDLEWARE_CLASSES

        django_settings.MIDDLEWARE_CLASSES = (
            'sentry.client.middleware.Sentry404CatchMiddleware',
        ) + django_settings.MIDDLEWARE_CLASSES

        resp = self.client.get('/non-existant-page')
        self.assertEquals(resp.status_code, 404)

        self.assertEquals(Message.objects.count(), 1)
        self.assertEquals(GroupedMessage.objects.count(), 1)
        last = Message.objects.get()
        self.assertEquals(last.url, u'http://testserver/non-existant-page')
        self.assertEquals(last.level, logging.INFO)
        self.assertEquals(last.logger, 'http404')

        django_settings.MIDDLEWARE_CLASSES = existing

    def test_response_error_id_middleware(self):
        # TODO: test with 500s
        existing = django_settings.MIDDLEWARE_CLASSES

        django_settings.MIDDLEWARE_CLASSES = (
            'sentry.client.middleware.SentryResponseErrorIdMiddleware',
            'sentry.client.middleware.Sentry404CatchMiddleware',
        ) + django_settings.MIDDLEWARE_CLASSES

        resp = self.client.get('/non-existant-page')
        self.assertEquals(resp.status_code, 404)
        headers = dict(resp.items())
        self.assertTrue(headers.get('X-Sentry-ID'))
        self.assertTrue(Message.objects.filter(message_id=headers['X-Sentry-ID']).exists())

        django_settings.MIDDLEWARE_CLASSES = existing

    def test_extra_storage(self):
        from sentry.utils import MockDjangoRequest

        request = MockDjangoRequest(
            META = {'foo': 'bar'},
        )

        logger = logging.getLogger()

        self.setUpHandler()

        logger.error('This is a test %s', 'error', extra={
            'request': request,
            'data': {
                'baz': 'bar',
            }
        })
        self.assertEquals(Message.objects.count(), 1)
        self.assertEquals(GroupedMessage.objects.count(), 1)
        last = Message.objects.get()
        self.assertEquals(last.logger, 'root')
        self.assertEquals(last.level, logging.ERROR)
        self.assertEquals(last.message, 'This is a test error')
        self.assertTrue('META' in last.data)
        self.assertTrue('foo' in last.data['META'])
        self.assertEquals(last.data['META']['foo'], 'bar')
        self.assertTrue('baz' in last.data)
        self.assertEquals(last.data['baz'], 'bar')

class SentryClientTest(TestCase):
    def setUp(self):
        self._client = settings.CLIENT

    def tearDown(self):
        settings.CLIENT = self._client

    def test_get_client(self):
        from sentry.client.log import LoggingSentryClient

        self.assertEquals(get_client().__class__, SentryClient)
        self.assertEquals(get_client(), get_client())

        settings.CLIENT = 'sentry.client.log.LoggingSentryClient'

        self.assertEquals(get_client().__class__, LoggingSentryClient)
        self.assertEquals(get_client(), get_client())

        settings.CLIENT = 'sentry.client.base.SentryClient'

class DjangoTest(BaseTest):
    def test_exception_handler(self):
        request = HttpRequest()

        try:
            raise ValueError('foo bar')
        except:
            sentry_exception_handler(request)

        self.assertTrue(hasattr(request, 'sentry'))

        event_id = request.sentry['id']

        event = Event.objects.get(event_id)

        data = event.data

        self.assertTrue('sentry.interfaces.Exception' in data)
        event_data = data['sentry.interfaces.Exception']
        self.assertTrue('value' in event_data)
        self.assertEquals(event_data['value'], 'foo bar')
        self.assertTrue('type' in event_data)
        self.assertEquals(event_data['type'], 'ValueError')

        self.assertTrue('sentry.interfaces.Stacktrace' in data)
        event_data = data['sentry.interfaces.Stacktrace']
        self.assertTrue('frames' in event_data)
        self.assertEquals(len(event_data['frames']), 1)
        frame = event_data['frames'][0]
        self.assertTrue('function' in frame)
        self.assertEquals(frame['function'], 'test_exception_handler')
        self.assertTrue('lineno' in frame)
        self.assertTrue(frame['lineno'] > 0)
        self.assertTrue('module' in frame)
        self.assertEquals(frame['module'], 'tests.test_contrib.django.test_django')
        self.assertTrue('id' in frame)
        self.assertTrue('filename' in frame)

    def test_django_testclient(self):
        from django.test import Client
        from django.template import TemplateSyntaxError
        c = Client()

        self.assertRaises(TemplateSyntaxError, c.get('/no_such_view/'))

        event = Event.objects.all()[0]
        data = event.data

        self.assertTrue('sentry.interfaces.Exception' in data)

        event_data = data['sentry.interfaces.Exception']

        self.assertTrue('type' in event_data)
        self.assertEquals(event_data['type'], 'TemplateSyntaxError')


        self.assertTrue('sentry.interfaces.Stacktrace' in data)
        event_data = data['sentry.interfaces.Stacktrace']
        self.assertEquals(len(event_data['frames']), 14)
