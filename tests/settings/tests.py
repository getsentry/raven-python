import socket

from unittest2 import TestCase
from raven.conf import settings

class SettingsTest(TestCase):
    def test_name(self):
        self.assertEquals(settings.NAME, socket.gethostname())
