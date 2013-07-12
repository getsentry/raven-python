"""
raven.contrib.django.raven.management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2013 by the Sentry Team, see AUTHORS for more details
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import, print_function

import sys

from functools import wraps

from django.conf import settings


def patch_base_command(cls):
    """
    Patches ``cls.execute``, returning a boolean describing if the
    attempt was successful.
    """
    try:
        original_func = cls.execute
    except AttributeError:
        # must not be a capable version of Django
        return False

    if hasattr(original_func, '__raven_patched'):
        return False

    def can_capture(cls):
        return 'sentry' not in settings.INSTALLED_APPS

    @wraps(original_func)
    def new_execute(self, *args, **kwargs):
        try:
            return original_func(self, *args, **kwargs)
        except Exception:

            if can_capture(type(self)):
                from raven.contrib.django.models import client

                client.captureException(extra={
                    'argv': sys.argv
                })
            raise

    new_execute.__raven_patched = True
    BaseCommand.execute = new_execute

    return True

if ('raven.contrib.django' in settings.INSTALLED_APPS
        or 'raven.contrib.django.raven_compat' in settings.INSTALLED_APPS):

    try:
        from django.core.management.base import BaseCommand
    except ImportError:
        # give up
        pass
    else:
        patch_base_command(BaseCommand)
