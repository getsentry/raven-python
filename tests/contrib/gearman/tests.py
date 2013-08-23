import mock

from raven.utils.testutils import TestCase
from raven.contrib.gearman import GearmanClient


class ClientTest(TestCase):
    def setUp(self):
        self.client = GearmanClient(servers=['http://example.com'])

    @mock.patch('raven.contrib.gearman.submit_job')
    def test_send_encoded(self, submit_job):
        self.client.send_encoded('foo')
        submit_job.assert_called_once_with('raven_gearman', data='{"message": "foo", "auth_header": null}')