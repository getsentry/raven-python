from sentry_client.base import SentryClient
from sentry_client.contrib.celery import tasks

class CelerySentryClient(SentryClient):
    def send(self, **kwargs):
        "Errors through celery"
        tasks.send.delay(kwargs)