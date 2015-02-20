from __future__ import absolute_import

import mock
import responses

from raven.utils.testutils import TestCase
from raven.base import Client


class RequestsTransportTest(TestCase):
    @responses.activate
    def test_does_send(self):
        responses.add(responses.POST, 'http://localhost:8143/api/1/store/')

        client = Client(
            dsn="requests+http://some_username:some_password@localhost:8143/1",
            raise_send_errors=True,
        )

        client.captureMessage(message='foo')

    @mock.patch('requests.Session.send')
    def test_passes_proxies(self, mock_send):
        client = Client(
            dsn="requests+http://some_username:some_password@localhost:8143/1?proxy=https://example.com",
            raise_send_errors=True,
        )

        client.captureMessage(message='foo')

        args, kwargs = mock_send.call_args
        request = args[0]
        assert request.url == 'http://localhost:8143/api/1/store/'
        assert kwargs['proxies'] == {'http': 'https://example.com'}
