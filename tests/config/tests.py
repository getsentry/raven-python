from __future__ import with_statement
import logging
import mock
import pytest
from raven.conf import load, setup_logging


class TestLoad(object):
    def test_basic(self):
        dsn = 'https://foo:bar@sentry.local/1'
        res = {}
        load(dsn, res)
        assert res == {
            'SENTRY_PROJECT': '1',
            'SENTRY_SERVERS': ['https://sentry.local/api/1/store/'],
            'SENTRY_PUBLIC_KEY': 'foo',
            'SENTRY_SECRET_KEY': 'bar',
        }

    def test_path(self):
        dsn = 'https://foo:bar@sentry.local/app/1'
        res = {}
        load(dsn, res)
        assert res == {
            'SENTRY_PROJECT': '1',
            'SENTRY_SERVERS': ['https://sentry.local/app/api/1/store/'],
            'SENTRY_PUBLIC_KEY': 'foo',
            'SENTRY_SECRET_KEY': 'bar',
        }

    def test_port(self):
        dsn = 'https://foo:bar@sentry.local:9000/app/1'
        res = {}
        load(dsn, res)
        assert res == {
            'SENTRY_PROJECT': '1',
            'SENTRY_SERVERS': ['https://sentry.local:9000/app/api/1/store/'],
            'SENTRY_PUBLIC_KEY': 'foo',
            'SENTRY_SECRET_KEY': 'bar',
        }

    def test_scope_is_optional(self):
        dsn = 'https://foo:bar@sentry.local/1'
        res = load(dsn)
        assert res == {
            'SENTRY_PROJECT': '1',
            'SENTRY_SERVERS': ['https://sentry.local/api/1/store/'],
            'SENTRY_PUBLIC_KEY': 'foo',
            'SENTRY_SECRET_KEY': 'bar',
        }

    def test_http(self):
        dsn = 'http://foo:bar@sentry.local/app/1'
        res = {}
        load(dsn, res)
        assert res == {
            'SENTRY_PROJECT': '1',
            'SENTRY_SERVERS': ['http://sentry.local/app/api/1/store/'],
            'SENTRY_PUBLIC_KEY': 'foo',
            'SENTRY_SECRET_KEY': 'bar',
        }

    def test_http_with_port(self):
        dsn = 'http://foo:bar@sentry.local:9000/app/1'
        res = {}
        load(dsn, res)
        assert res == {
            'SENTRY_PROJECT': '1',
            'SENTRY_SERVERS': ['http://sentry.local:9000/app/api/1/store/'],
            'SENTRY_PUBLIC_KEY': 'foo',
            'SENTRY_SECRET_KEY': 'bar',
        }

    def test_https_port_443(self):
        dsn = 'https://foo:bar@sentry.local:443/app/1'
        res = {}
        load(dsn, res)
        assert res == {
            'SENTRY_PROJECT': '1',
            'SENTRY_SERVERS': ['https://sentry.local/app/api/1/store/'],
            'SENTRY_PUBLIC_KEY': 'foo',
            'SENTRY_SECRET_KEY': 'bar',
        }

    def test_https_port_80(self):
        dsn = 'https://foo:bar@sentry.local:80/app/1'
        res = {}
        load(dsn, res)
        assert res == {
            'SENTRY_PROJECT': '1',
            'SENTRY_SERVERS': ['https://sentry.local:80/app/api/1/store/'],
            'SENTRY_PUBLIC_KEY': 'foo',
            'SENTRY_SECRET_KEY': 'bar',
        }

    def test_udp(self):
        dsn = 'udp://foo:bar@sentry.local:9001/1'
        res = {}
        load(dsn, res)
        assert res == {
            'SENTRY_PROJECT': '1',
            'SENTRY_SERVERS': ['udp://sentry.local:9001/api/1/store/'],
            'SENTRY_PUBLIC_KEY': 'foo',
            'SENTRY_SECRET_KEY': 'bar',
        }

    def test_missing_netloc(self):
        with pytest.raises(ValueError):
            load('https://foo:bar@/1')

    def test_missing_project(self):
        with pytest.raises(ValueError):
            load('https://foo:bar@example.com')

    def test_missing_public_key(self):
        with pytest.raises(ValueError):
            load('https://:bar@example.com')

    def test_missing_secret_key(self):
        with pytest.raises(ValueError):
            load('https://bar@example.com')

    def test_invalid_scheme(self):
        with pytest.raises(ValueError):
            load('ftp://foo:bar@sentry.local/1')


class TestSetupLogging(object):
    def test_basic_not_configured(self):
        with mock.patch('logging.getLogger', spec=logging.getLogger) as getLogger:
            logger = getLogger()
            logger.handlers = []
            handler = mock.Mock()
            result = setup_logging(handler)
            assert result

    def test_basic_already_configured(self):
        with mock.patch('logging.getLogger', spec=logging.getLogger) as getLogger:
            handler = mock.Mock()
            logger = getLogger()
            logger.handlers = [handler]
            result = setup_logging(handler)
            assert not result
