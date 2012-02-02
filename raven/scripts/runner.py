"""
raven.scripts.runner
~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import

import os
import sys

from raven import Client


def main():
    dsn = ' '.join(sys.argv[2:])
    if not (dsn or os.environ.get('SENTRY_DSN')):
        print "Error: No configuration detected!"
        print "You must either pass a DSN to the command, or set the SENTRY_DSN environment variable."
        sys.exit(1)

    print "Using DSN configuration:"
    print " ", dsn
    print

    client = Client(dsn)

    print "Client configuration:"
    for k in ('servers', 'project', 'public_key', 'secret_key'):
        print '  %-15s: %s' % (k, getattr(client, k))
    print

    if not all([client.servers, client.project, client.public_key, client.secret_key]):
        print "Error: All values must be set!"
        sys.exit(1)

    print 'Sending a test message...',
    ident = client.get_ident(client.message('This is a test message generated using ``raven test``'))
    print 'success!'
    print
    print 'The test message can be viewed at the following URL:'
    url = client.servers[0].split('/api/store/', 1)[0]
    print '  %s/%s/search/?q=%s' % (url, client.project, ident)
