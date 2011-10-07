from sentry_client.base import Client
from sentry_client.contrib.celery import tasks

class CeleryClient(Client):
    def send(self, **kwargs):
        "Errors through celery"
        tasks.send.delay(kwargs)