import socket

from unittest2 import TestCase
from sentry_client.conf import settings

class SettingsTest(TestCase):
    def test_name(self):
        self.assertEquals(settings.NAME, socket.gethostname())
