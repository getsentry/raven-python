from __future__ import with_statement

import logging
import mock

from raven.conf import setup_logging
from raven.conf.remote import RemoteConfig
from raven.exceptions import InvalidDsn
from raven.utils import get_auth_header
from raven.utils.testutils import TestCase


class RemoteConfigTest(TestCase):
    def test_path_strip(self):
        dsn = 'https://foo:bar@sentry.local/app/1\n'
        res = RemoteConfig.from_string(dsn)
        assert res.project == '1'
        assert res.base_url == 'https://sentry.local/app'
        assert res.store_endpoint == 'https://sentry.local/app/api/1/store/'
        assert res.public_key == 'foo'
        assert res.secret_key == 'bar'
        assert res.options == {}

    def test_path(self):
        dsn = 'https://foo:bar@sentry.local/app/1'
        res = RemoteConfig.from_string(dsn)
        assert res.project == '1'
        assert res.base_url == 'https://sentry.local/app'
        assert res.store_endpoint == 'https://sentry.local/app/api/1/store/'
        assert res.public_key == 'foo'
        assert res.secret_key == 'bar'
        assert res.options == {}

    def test_http(self):
        dsn = 'http://foo:bar@sentry.local/1'
        res = RemoteConfig.from_string(dsn)
        assert res.project == '1'
        assert res.base_url == 'http://sentry.local'
        assert res.store_endpoint == 'http://sentry.local/api/1/store/'
        assert res.public_key == 'foo'
        assert res.secret_key == 'bar'
        assert res.options == {}

    def test_http_with_port(self):
        dsn = 'http://foo:bar@sentry.local:9000/1'
        res = RemoteConfig.from_string(dsn)
        assert res.project == '1'
        assert res.base_url == 'http://sentry.local:9000'
        assert res.store_endpoint == 'http://sentry.local:9000/api/1/store/'
        assert res.public_key == 'foo'
        assert res.secret_key == 'bar'
        assert res.options == {}

    def test_https(self):
        dsn = 'https://foo:bar@sentry.local/1'
        res = RemoteConfig.from_string(dsn)
        assert res.project == '1'
        assert res.base_url == 'https://sentry.local'
        assert res.store_endpoint == 'https://sentry.local/api/1/store/'
        assert res.public_key == 'foo'
        assert res.secret_key == 'bar'
        assert res.options == {}

    def test_https_with_port(self):
        dsn = 'https://foo:bar@sentry.local:9000/app/1'
        res = RemoteConfig.from_string(dsn)
        assert res.project == '1'
        assert res.base_url == 'https://sentry.local:9000/app'
        assert res.store_endpoint == 'https://sentry.local:9000/app/api/1/store/'
        assert res.public_key == 'foo'
        assert res.secret_key == 'bar'
        assert res.options == {}

    def test_options(self):
        dsn = 'http://foo:bar@sentry.local/1?timeout=1'
        res = RemoteConfig.from_string(dsn)
        assert res.project == '1'
        assert res.base_url == 'http://sentry.local'
        assert res.store_endpoint == 'http://sentry.local/api/1/store/'
        assert res.public_key == 'foo'
        assert res.secret_key == 'bar'
        assert res.options == {'timeout': '1'}

    def test_no_secret_key(self):
        dsn = 'https://foo@sentry.local/1'
        res = RemoteConfig.from_string(dsn)
        assert res.project == '1'
        assert res.base_url == 'https://sentry.local'
        assert res.store_endpoint == 'https://sentry.local/api/1/store/'
        assert res.public_key == 'foo'
        assert res.secret_key is None
        assert res.options == {}
        assert res.is_active()

        assert get_auth_header(protocol=7, timestamp=42,
                               client='raven-python/1.0',
                               api_key=res.public_key) == (
            'Sentry sentry_timestamp=42, sentry_client=raven-python/1.0, '
            'sentry_version=7, sentry_key=foo')

    def test_missing_netloc(self):
        dsn = 'https://foo:bar@/1'
        self.assertRaises(InvalidDsn, RemoteConfig.from_string, dsn)

    def test_missing_project(self):
        dsn = 'https://foo:bar@example.com'
        self.assertRaises(InvalidDsn, RemoteConfig.from_string, dsn)

    def test_missing_public_key(self):
        dsn = 'https://:bar@example.com'
        self.assertRaises(InvalidDsn, RemoteConfig.from_string, dsn)

    def test_invalid_scheme(self):
        dsn = 'ftp://foo:bar@sentry.local/1'
        self.assertRaises(InvalidDsn, RemoteConfig.from_string, dsn)

    def test_get_public_dsn(self):
        res = RemoteConfig(
            base_url='http://example.com',
            project='1',
            public_key='public',
            secret_key='secret',
        )
        public_dsn = res.get_public_dsn()
        assert public_dsn == '//public@example.com/1'


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
