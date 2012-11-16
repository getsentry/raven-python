"""
This is an alternate client to raven.contrib.django.DjangoClient
which forces data to be routed through the settings.METLOG
"""

from __future__ import absolute_import
from raven.contrib.django.client import DjangoClient

try:
    from django.conf import settings
    from metlog.client import SEVERITY
except:
    settings = None  # NOQA
    SEVERITY = None  # NOQA

class MetlogDjangoClient(DjangoClient):
    """
    This client simply overrides the send_encoded method in the base
    Client so that we use settings.METLOG for transmission
    """
    def send_encoded(self, message, public_key=None, \
            auth_header=None, **kwargs):
        """
        Given an already serialized message send it off to metlog
        """

        settings.METLOG.metlog(type='sentry',
                logger='raven.contrib.django.metlog',
                payload=message,
                severity=SEVERITY.ERROR)
