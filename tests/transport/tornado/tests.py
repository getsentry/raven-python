from __future__ import absolute_import

import mock

from raven.base import Client
from raven.utils.testutils import TestCase


class TornadoTransportTests(TestCase):
    @mock.patch("raven.transport.tornado.HTTPClient")
    def test_send(self, fake_client):
        url = "https://user:pass@host:1234/1"
        timeout = 1
        verify_ssl = 1
        ca_certs = "/some/path/somefile"

        fake = fake_client.return_value
        raven_client = Client(
            dsn="tornado+{0}?timeout={1}&verify_ssl={2}&ca_certs={3}".
            format(url, timeout, verify_ssl, ca_certs))

        raven_client.captureMessage(message="test")

        # make sure an instance of HTTPClient was created, since we are not in
        # an IOLoop
        fake_client.assert_called_once_with()
        fake_fetch = fake.fetch

        # make sure we called fetch() which does the sending
        self.assertEqual(fake_fetch.call_count, 1)
        # only verify the special kwargs that we should be passing through,
        # no need to verify the urls and whatnot
        args, kwargs = fake_fetch.call_args
        self.assertEqual(kwargs["connect_timeout"], timeout)
        self.assertEqual(kwargs["validate_cert"], bool(verify_ssl))
        self.assertEqual(kwargs["ca_certs"], ca_certs)
