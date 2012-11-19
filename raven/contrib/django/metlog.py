"""
raven.contrib.django.client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import
from raven.base import Client
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
    def is_enabled(self):
        return True

    def send(self, **kwargs):
        """
        Serializes and signs ``data`` and passes the payload off to ``send_remote``

        raven.contrib.django.client.DjangoClient does a check for
        self.servers, just bypass that and delegate to the primary
        raven.base.Client base class which will juse encode and fwd
        the data on to send_encoded.
        """
        return Client.send(self, **kwargs)

    def send_encoded(self, message, public_key=None, \
            auth_header=None, **kwargs):
        """
        Given an already serialized message send it off to metlog
        """
        settings.METLOG.metlog(type='sentry',
                logger='raven.contrib.django.metlog',
                payload=message,
                severity=SEVERITY.ERROR)
