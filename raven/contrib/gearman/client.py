from django_gearman_commands import submit_job

from raven.contrib.django.client import DjangoClient
from raven.contrib.gearman import RAVEN_GEARMAN_JOB_NAME

__all__ = ('GearmanClient',)


class GearmanClient(DjangoClient):

    def send_encoded(self, message, auth_header=None, **kwargs):
        return submit_job(RAVEN_GEARMAN_JOB_NAME, data=message)