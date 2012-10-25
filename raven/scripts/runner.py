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
from optparse import OptionParser

from raven import Client
from raven.utils.json import json


def store_json(option, opt_str, value, parser):
    try:
        value = json.loads(value)
    except ValueError:
        print "Invalid JSON was used for option %s.  Received: %s" % (opt_str, value)
        sys.exit(1)
    setattr(parser.values, option.dest, value)


def main():
    root = logging.getLogger('sentry.errors')
    root.setLevel(logging.DEBUG)
    root.addHandler(logging.StreamHandler())

    parser = OptionParser()
    parser.add_option("--data", action="callback", callback=store_json,
        type="string", nargs=1, dest="data")
    parser.add_option("--tags", action="callback", callback=store_json,
        type="string", nargs=1, dest="tags")
    (opts, args) = parser.parse_args()

    dsn = ' '.join(args[1:]) or os.environ.get('SENTRY_DSN')
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

    data = opts.data or {
        'culprit': 'raven.scripts.runner',
        'logger': 'raven.test',
        'sentry.interfaces.Http': {
            'method': 'GET',
            'url': 'http://example.com',
        }
    }

    print 'Sending a test message...',
    ident = client.get_ident(client.captureMessage(
        message='This is a test message generated using ``raven test``',
        data=data,
        level=logging.INFO,
        stack=True,
        tags=opts.tags,
        extra={
            'user': pwd.getpwuid(os.geteuid())[0],
            'loadavg': os.getloadavg(),
        },
    ))

    if client.state.did_fail():
        print 'error!'
        return False

    print 'success!'
    print
    print 'The test message can be viewed at the following URL:'
    url = client.servers[0].split('/api/store/', 1)[0]
    print '  %s/%s/search/?q=%s' % (url, client.project, ident)
