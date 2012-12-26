import mock
import sys
from exam import fixture
from unittest2 import TestCase

from raven.context import Context


class ContextTest(TestCase):
    @fixture
    def client(self):
        return mock.Mock()

    def context(self, **kwargs):
        return Context(self.client, **kwargs)

    def test_capture_exception(self):
        with self.context(tags={'foo': 'bar'}) as client:
            result = client.captureException('exception')
            self.assertEquals(result, self.client.captureException.return_value)
            self.client.captureException.assert_called_once_with('exception', tags={
                'foo': 'bar',
            })

    def test_capture_message(self):
        with self.context(tags={'foo': 'bar'}) as client:
            result = client.captureMessage('exception')
            self.assertEquals(result, self.client.captureMessage.return_value)
            self.client.captureMessage.assert_called_once_with('exception', tags={
                'foo': 'bar',
            })

    def test_implicit_exception_handling(self):
        try:
            with self.context(tags={'foo': 'bar'}):
                try:
                    1 / 0
                except Exception:
                    exc_info = sys.exc_info()
                    raise
        except Exception:
            pass

        self.client.captureException.assert_called_once_with(exc_info, tags={
            'foo': 'bar',
        })