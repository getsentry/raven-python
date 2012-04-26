"""
raven.contrib.django.celery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from raven.contrib.celery import CeleryMixin
from raven.contrib.django import DjangoClient
try:
    from celery.task import task
except ImportError:
    from celery.decorators import task

class CeleryClient(CeleryMixin, DjangoClient):
    def send_integrated(self, kwargs):
        self.send_raw_integrated.delay(kwargs)

    @task(routing_key='sentry')
    def send_raw_integrated(self, kwargs):
        super(CeleryClient, self).send_integrated(kwargs)
