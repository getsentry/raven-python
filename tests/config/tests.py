from __future__ import with_statement
import logging
import mock
from raven.conf import load, setup_logging
from raven.utils.testutils import TestCase


class LoadTest(TestCase):
    def test_basic(self):
        dsn = 'https://foo:bar@sentry.local/1'
        res = {}
        load(dsn, res)
        self.assertEquals(res, {
            'SENTRY_PROJECT': '1',
            'SENTRY_SERVERS': ['https://sentry.local/api/1/store/'],
            'SENTRY_PUBLIC_KEY': 'foo',
            'SENTRY_SECRET_KEY': 'bar',
            'SENTRY_TRANSPORT_OPTIONS': {},
        })

    def test_path(self):
        dsn = 'https://foo:bar@sentry.local/app/1'
        res = {}
        load(dsn, res)
        self.assertEquals(res, {
            'SENTRY_PROJECT': '1',
            'SENTRY_SERVERS': ['https://sentry.local/app/api/1/store/'],
            'SENTRY_PUBLIC_KEY': 'foo',
            'SENTRY_SECRET_KEY': 'bar',
            'SENTRY_TRANSPORT_OPTIONS': {},
        })

    def test_port(self):
        dsn = 'https://foo:bar@sentry.local:9000/app/1'
        res = {}
        load(dsn, res)
        self.assertEquals(res, {
            'SENTRY_PROJECT': '1',
            'SENTRY_SERVERS': ['https://sentry.local:9000/app/api/1/store/'],
            'SENTRY_PUBLIC_KEY': 'foo',
            'SENTRY_SECRET_KEY': 'bar',
            'SENTRY_TRANSPORT_OPTIONS': {},
        })

    def test_scope_is_optional(self):
        dsn = 'https://foo:bar@sentry.local/1'
        res = load(dsn)
        self.assertEquals(res, {
            'SENTRY_PROJECT': '1',
            'SENTRY_SERVERS': ['https://sentry.local/api/1/store/'],
            'SENTRY_PUBLIC_KEY': 'foo',
            'SENTRY_SECRET_KEY': 'bar',
            'SENTRY_TRANSPORT_OPTIONS': {},
        })

    def test_http(self):
        dsn = 'http://foo:bar@sentry.local/app/1'
        res = {}
        load(dsn, res)
        self.assertEquals(res, {
            'SENTRY_PROJECT': '1',
            'SENTRY_SERVERS': ['http://sentry.local/app/api/1/store/'],
            'SENTRY_PUBLIC_KEY': 'foo',
            'SENTRY_SECRET_KEY': 'bar',
            'SENTRY_TRANSPORT_OPTIONS': {},
        })

    def test_http_with_port(self):
        dsn = 'http://foo:bar@sentry.local:9000/app/1'
        res = {}
        load(dsn, res)
        self.assertEquals(res, {
            'SENTRY_PROJECT': '1',
            'SENTRY_SERVERS': ['http://sentry.local:9000/app/api/1/store/'],
            'SENTRY_PUBLIC_KEY': 'foo',
            'SENTRY_SECRET_KEY': 'bar',
            'SENTRY_TRANSPORT_OPTIONS': {},
        })

    def test_udp(self):
        dsn = 'udp://foo:bar@sentry.local:9001/1'
        res = {}
        load(dsn, res)
        self.assertEquals(res, {
            'SENTRY_PROJECT': '1',
            'SENTRY_SERVERS': ['udp://sentry.local:9001/api/1/store/'],
            'SENTRY_PUBLIC_KEY': 'foo',
            'SENTRY_SECRET_KEY': 'bar',
            'SENTRY_TRANSPORT_OPTIONS': {},
        })

    def test_options(self):
        dsn = 'http://foo:bar@sentry.local:9001/1?timeout=1'
        res = {}
        load(dsn, res)
        self.assertEquals(res, {
            'SENTRY_PROJECT': '1',
            'SENTRY_SERVERS': ['http://sentry.local:9001/api/1/store/'],
            'SENTRY_PUBLIC_KEY': 'foo',
            'SENTRY_SECRET_KEY': 'bar',
            'SENTRY_TRANSPORT_OPTIONS': {'timeout': '1'},
        })

    def test_missing_netloc(self):
        dsn = 'https://foo:bar@/1'
        self.assertRaises(ValueError, load, dsn)

    def test_missing_project(self):
        dsn = 'https://foo:bar@example.com'
        self.assertRaises(ValueError, load, dsn)

    def test_missing_public_key(self):
        dsn = 'https://:bar@example.com'
        self.assertRaises(ValueError, load, dsn)

    def test_missing_secret_key(self):
        dsn = 'https://bar@example.com'
        self.assertRaises(ValueError, load, dsn)

    def test_invalid_scheme(self):
        dsn = 'ftp://foo:bar@sentry.local/1'
        self.assertRaises(ValueError, load, dsn)


class SetupLoggingTest(TestCase):
    def test_basic_not_configured(self):
        with mock.patch('logging.getLogger', spec=logging.getLogger) as getLogger:
            logger = getLogger()
            logger.handlers = []
            handler = mock.Mock()
            result = setup_logging(handler)
            self.assertTrue(result)

    def test_basic_already_configured(self):
        with mock.patch('logging.getLogger', spec=logging.getLogger) as getLogger:
            handler = mock.Mock()
            logger = getLogger()
            logger.handlers = [handler]
            result = setup_logging(handler)
            self.assertFalse(result)
