"""
raven.contrib.celery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from celery.decorators import task

class _EmptyClass(object):
    pass

def make_celery_client_class(parent):
    class CeleryClient(parent):
        def send(self, **kwargs):
            "Errors through celery"
            self.send_remote.delay(kwargs)

        @task(routing_key='sentry')
        def send_remote(self, data):
            return super(CeleryClient, self).send(**data)
    return CeleryClient

def make_celery_client(client):
    cls = make_celery_client_class(client.__class__)
    new_client = _EmptyClass()
    new_client.__class__ = cls
    new_client.__dict__.update(client.__dict__)
    return new_client