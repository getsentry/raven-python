from raven.conf import load
from unittest2 import TestCase


class LoadTest(TestCase):
    def test_basic(self):
        dsn = 'https://foo:bar@sentry.local/1'
        res = {}
        load(dsn, res)
        self.assertEquals(res, {
            'SENTRY_PROJECT': '1',
            'SENTRY_SERVERS': ['https://sentry.local/api/store/'],
            'SENTRY_PUBLIC_KEY': 'foo',
            'SENTRY_SECRET_KEY': 'bar',
        })
