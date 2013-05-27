from django_gearman_commands import GearmanWorkerBaseCommand

from django.conf import settings

from raven.contrib.django.models import get_client
from raven.contrib.gearman import RAVEN_GEARMAN_JOB_NAME


class Command(GearmanWorkerBaseCommand):

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
        return self.client.send_encoded(job_data)
