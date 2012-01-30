"""
raven.contrib.django.celery.tasks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

# TODO: need to educate myself on how this works

from raven.contrib.django.models import get_client

# We just need to pull in the client to ensure the task is registered
client = get_client()
