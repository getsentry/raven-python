"""
raven.contrib.pylons
~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from raven.middleware import Sentry as Middleware
from raven.base import Client


def list_from_setting(config, setting):
    value = config.get(setting)
    if not value:
        return None
    return value.split()


class Sentry(Middleware):
    def __init__(self, app, config, client_cls=Client):
        client = client_cls(
            dsn=config.get('sentry.dsn'),
            servers=list_from_setting(config, 'sentry.servers'),
            name=config.get('sentry.name'),
            key=config.get('sentry.key'),
            public_key=config.get('sentry.public_key'),
            secret_key=config.get('sentry.secret_key'),
            project=config.get('sentry.project'),
            site=config.get('sentry.site'),
            include_paths=list_from_setting(config, 'sentry.include_paths'),
            exclude_paths=list_from_setting(config, 'sentry.exclude_paths'),
        )
        super(Sentry, self).__init__(app, client)
