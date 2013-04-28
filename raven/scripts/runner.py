"""
raven.scripts.runner
~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

from __future__ import absolute_import
from __future__ import print_function

import logging
import os
import sys
from optparse import OptionParser

from raven import Client
from raven.utils.json import json


def store_json(option, opt_str, value, parser):
    try:
        value = json.loads(value)
    except ValueError:
        print("Invalid JSON was used for option %s.  Received: %s" % (opt_str, value))
        sys.exit(1)
    setattr(parser.values, option.dest, value)


def get_loadavg():
    if hasattr(os, 'getloadavg'):
        return os.getloadavg()
    return None


def get_uid():
    try:
        import pwd
    except ImportError:
        return None
    return pwd.getpwuid(os.geteuid())[0]


def send_test_message(client, options):
    print("Client configuration:")
    for k in ('servers', 'project', 'public_key', 'secret_key'):
        print('  %-15s: %s' % (k, getattr(client, k)))
    print()

    if not all([client.servers, client.project, client.public_key, client.secret_key]):
        print("Error: All values must be set!")
        sys.exit(1)

    if not client.is_enabled():
        print('Error: Client reports as being disabled!')
        sys.exit(1)

    data = options.get('data', {
        'culprit': 'raven.scripts.runner',
        'logger': 'raven.test',
        'sentry.interfaces.Http': {
            'method': 'GET',
            'url': 'http://example.com',
        }
    })

    print('Sending a test message...',)

    ident = client.get_ident(client.captureMessage(
        message='This is a test message generated using ``raven test``',
        data=data,
        level=logging.INFO,
        stack=True,
        tags=options.get('tags', {}),
        extra={
            'user': get_uid(),
            'loadavg': get_loadavg(),
        },
    ))

    if client.state.did_fail():
        print('error!')
        return False

    print('success!')
    print('Event ID was %r' % (ident,))


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
        print("Error: No configuration detected!")
        print("You must either pass a DSN to the command, or set the SENTRY_DSN environment variable.")
        sys.exit(1)

    print("Using DSN configuration:")
    print(" ", dsn)
    print()

    client = Client(dsn, include_paths=['raven'])
    send_test_message(client, opts.__dict__)
