from raven.middleware import Sentry
from raven.base import Client


def sentry_filter_factory(app, global_conf, **kwargs):
    client = Client(**kwargs)
    return Sentry(app, client)
