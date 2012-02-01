"""
raven.contrib.celery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from celery.decorators import task
from raven.base import Client


class CeleryMixin(object):
    def send_encoded(self, message):
        "Errors through celery"
        self.send_raw.delay(message)

    @task(routing_key='sentry')
    def send_raw(self, message):
        return super(CeleryMixin, self).send_encoded(message)


class CeleryClient(CeleryMixin, Client):
    pass

