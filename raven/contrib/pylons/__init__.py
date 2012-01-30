"""
raven.contrib.pylons
~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from raven.middleware import Sentry as Middleware
from raven.base import Client


class Sentry(Middleware):

    def __init__(self, app, config):
        if not config.get('sentry.servers'):
            raise TypeError('The sentry.servers config variable is required')

        client = Client(
            servers=config['sentry.servers'].split(),
            name=config.get('sentry.name'),
            key=config.get('sentry.key'),
            public_key=config.get('sentry.public_key'),
            secret_key=config.get('sentry.secret_key'),
            project=config.get('sentry.site_project'),
            site=config.get('sentry.site_name'),
            include_paths=config.get(
                'sentry.include_paths', '').split() or None,
            exclude_paths=config.get(
                'sentry.exclude_paths', '').split() or None,
        )
        super(Sentry, self).__init__(app, client)
