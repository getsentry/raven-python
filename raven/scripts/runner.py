"""
raven.scripts.runner
~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import logging
import os
import sys
import pwd

from raven import Client


def main():
    root = logging.getLogger('sentry.errors')
    root.setLevel(logging.DEBUG)
    root.addHandler(logging.StreamHandler())

    dsn = ' '.join(sys.argv[2:]) or os.environ.get('SENTRY_DSN')
    if not dsn:
        print "Error: No configuration detected!"
        print "You must either pass a DSN to the command, or set the SENTRY_DSN environment variable."
        sys.exit(1)

    print "Using DSN configuration:"
    print " ", dsn
    print

    client = Client(dsn, include_paths=['raven'])

    print "Client configuration:"
    for k in ('servers', 'project', 'public_key', 'secret_key'):
        print '  %-15s: %s' % (k, getattr(client, k))
    print

    if not all([client.servers, client.project, client.public_key, client.secret_key]):
        print "Error: All values must be set!"
        sys.exit(1)

    print 'Sending a test message...',
    ident = client.get_ident(client.captureMessage(
        message='This is a test message generated using ``raven test``',
        data={
            'culprit': 'raven.scripts.runner',
            'logger': 'raven.test',
            'sentry.interfaces.Http': {
                'method': 'GET',
                'url': 'http://example.com',
            }
        },
        level=logging.INFO,
        stack=True,
        extra={
            'user': pwd.getpwuid(os.geteuid())[0],
            'loadavg': os.getloadavg(),
        }
    ))
    print 'success!'
    print
    print 'The test message can be viewed at the following URL:'
    url = client.servers[0].split('/api/store/', 1)[0]
    print '  %s/%s/search/?q=%s' % (url, client.project, ident)
