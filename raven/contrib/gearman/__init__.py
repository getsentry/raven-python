import json

from django_gearman_commands import submit_job

from raven.base import Client

__all__ = ('RAVEN_GEARMAN_JOB_NAME', 'GearmanMixin', 'GearmanClient')


RAVEN_GEARMAN_JOB_NAME = 'raven_gearman'


class GearmanMixin(object):
    """This class servers as a Mixin for client implementations that wants to support gearman async queue."""

    def send_encoded(self, message, auth_header=None, **kwargs):
        """Encoded data are sent to gearman, instead of directly sent to the sentry server.

        :param message: encoded message
        :type message: string
        :param auth_header: auth_header: authentication header for sentry
        :type auth_header: string
        :returns: void
        :rtype: None

        """
        payload = json.dumps({
            'message': message,
            'auth_header': auth_header
        })
        submit_job(RAVEN_GEARMAN_JOB_NAME, data=payload)


class GearmanClient(GearmanMixin, Client):
    """Independent implementation of gearman client for raven."""