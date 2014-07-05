from __future__ import absolute_import

import mock

from raven.utils.testutils import TestCase
from raven.base import Client


class RequestsTransportTest(TestCase):
    def setUp(self):
        self.client = Client(
            dsn="requests+http://some_username:some_password@localhost:8143/1",
        )

    @mock.patch('raven.transport.requests.post')
    def test_does_send(self, post):
        self.client.captureMessage(message='foo')
        self.assertEqual(post.call_count, 1)
        expected_url = 'http://localhost:8143/api/1/store/'
        self.assertEqual(expected_url, post.call_args[0][0])
