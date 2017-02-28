from __future__ import absolute_import

import mock

from raven.base import Client
from tornado import gen, testing, httpclient


class TornadoTransportTests(testing.AsyncTestCase):

    def get_new_ioloop(self):
        io_loop = super(TornadoTransportTests, self).get_new_ioloop()
        io_loop.make_current()
        return io_loop

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

    @testing.gen_test
    def test__sending_with_error_calls_error_callback(self):
        c = Client(dsn='tornado+http://uver:pass@localhost:46754/1')

        with mock.patch.object(Client, '_failed_send') as mock_failed:
            c.captureMessage(message='test')
            yield gen.sleep(0.01)  # we need to run after the async send

            assert mock_failed.called

    @testing.gen_test
    def test__sending_successfully_calls_success_callback(self):
        c = Client(dsn='tornado+http://uver:pass@localhost:46754/1')
        with mock.patch.object(Client, '_successful_send') as mock_successful:
            with mock.patch.object(httpclient.AsyncHTTPClient, 'fetch') as mock_fetch:
                mock_fetch.return_value = gen.maybe_future(True)
                c.captureMessage(message='test')
                yield gen.sleep(0.01)  # we need to run after the async send

                assert mock_successful.called
