from raven.base import Client
from raven.contrib.celery import tasks

class CeleryClient(Client):
    def send(self, **kwargs):
        "Errors through celery"
        tasks.send.delay(kwargs)