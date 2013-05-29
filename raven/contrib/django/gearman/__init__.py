import json

from django_gearman_commands import GearmanWorkerBaseCommand

from django.conf import settings

from raven.contrib.gearman import GearmanMixin, RAVEN_GEARMAN_JOB_NAME
from raven.contrib.django import DjangoClient
from raven.contrib.django.models import get_client

__all__ = ('GearmanClient', 'GearmanWorkerCommand')


class GearmanClient(GearmanMixin, DjangoClient):
    """Gearman client implementation for django applications."""


class GearmanWorkerCommand(GearmanWorkerBaseCommand):
    """Gearman worker implementation.

    This worker is run as django management command. Gearman client send messages to gearman deamon. Next
    the messages are downloaded from gearman daemon by this worker, and sent to sentry server by standrd
    django raven client 'raven.contrib.django.client.DjangoClient', if not specified otherwise by
    SENTRY_GEARMAN_CLIENT django setting.

    This worker is dependent on django-gearman-commands app. For more information how this works, please
    visit https://github.com/CodeScaleInc/django-gearman-commands.

    """

    _client = None

    @property
    def task_name(self):
        return RAVEN_GEARMAN_JOB_NAME

    @property
    def client(self):
        if self._client is None:
            self._client = get_client(getattr(settings, 'SENTRY_GEARMAN_CLIENT',
                                              'raven.contrib.django.client.DjangoClient'))
        return self._client

    def do_job(self, job_data):
        payload = json.loads(job_data)
        return self.client.send_encoded(payload['message'], auth_header=payload['auth_header'])
