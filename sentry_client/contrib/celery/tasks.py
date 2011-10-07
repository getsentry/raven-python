"""
sentry_client.contrib.celery.tasks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from celery.decorators import task
from sentry_client.conf import settings
from sentry_client.base import Client

@task(routing_key=getattr(settings, 'CELERY_ROUTING_KEY', None))
def send(data):
    return Client().send(**data)
