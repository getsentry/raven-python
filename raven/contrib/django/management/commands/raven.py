"""
raven.contrib.django.management.commands.raven
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2013 by the Sentry Team, see AUTHORS for more details
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import, print_function

from django.core.management.base import BaseCommand
from optparse import make_option
from raven.scripts.runner import store_json, send_test_message
import sys


class Command(BaseCommand):
    help = 'Commands to interact with the Sentry client'

    option_list = BaseCommand.option_list + (
        make_option(
            "--data", action="callback", callback=store_json,
            type="string", nargs=1, dest="data"),
        make_option(
            "--tags", action="callback", callback=store_json,
            type="string", nargs=1, dest="tags"),
    )

    def handle(self, *args, **options):
        if len(args) != 1 or args[0] != 'test':
            print('Usage: manage.py raven test')
            sys.exit(1)

        from raven.contrib.django.models import client

        send_test_message(client, options)
